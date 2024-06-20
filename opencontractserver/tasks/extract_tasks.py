import logging

import marvin
import numpy as np
from celery import chord, group, shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from llama_index.core import Settings, VectorStoreIndex, QueryBundle
from llama_index.core.agent import FunctionCallingAgentWorker, StructuredPlannerAgent
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.schema import NodeWithScore, Node
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.llms.openai import OpenAI
from llama_index_client import TextNode
from pgvector.django import CosineDistance
from pydantic import BaseModel

from opencontractserver.annotations.models import Annotation
from opencontractserver.extracts.models import Datacell, Extract
from opencontractserver.llms.vector_stores import DjangoAnnotationVectorStore
from opencontractserver.types.enums import PermissionTypes
from opencontractserver.utils.embeddings import calculate_embedding_for_text
from opencontractserver.utils.etl import parse_model_or_primitive
from opencontractserver.utils.permissioning import set_permissions_for_obj_to_user

logger = logging.getLogger(__name__)

# Pass OpenAI API key to marvin for parsing / extract
marvin.settings.openai.api_key = settings.OPENAI_API_KEY


@shared_task
def mark_extract_complete(extract_id):
    extract = Extract.objects.get(pk=extract_id)
    extract.finished = timezone.now()
    extract.save()


@shared_task
def run_extract(extract_id, user_id):
    logger.info(f"Run extract for extract {extract_id}")

    extract = Extract.objects.get(pk=extract_id)

    with transaction.atomic():
        extract.started = timezone.now()
        extract.save()

    fieldset = extract.fieldset

    document_ids = extract.documents.all().values_list("id", flat=True)
    print(f"Run extract {extract_id} over document ids {document_ids}")
    tasks = []

    for document_id in document_ids:
        for column in fieldset.columns.all():
            with transaction.atomic():
                cell = Datacell.objects.create(
                    extract=extract,
                    column=column,
                    data_definition=column.output_type,
                    creator_id=user_id,
                    document_id=document_id,
                )
                set_permissions_for_obj_to_user(user_id, cell, [PermissionTypes.CRUD])

                # Kick off processing job for cell in queue as soon as it's created.
                tasks.append(llama_index_doc_query.si(cell.pk))

    chord(group(*tasks))(mark_extract_complete.si(extract_id))


@shared_task
def llama_index_doc_query(cell_id, similarity_top_k=15, max_token_length: int = 512):
    """
    Use LlamaIndex to run queries specified for a particular cell
    """

    datacell = Datacell.objects.get(id=cell_id)
    print(f"Process datacell {datacell}")

    try:

        datacell.started = timezone.now()
        datacell.save()

        document = datacell.document
        embed_model = HuggingFaceEmbedding(
            model_name="multi-qa-MiniLM-L6-cos-v1", cache_folder="/models"
        )  # Using our pre-load cache path where the model was stored on container build
        Settings.embed_model = embed_model

        llm = OpenAI(model=settings.OPENAI_MODEL, api_key=settings.OPENAI_API_KEY)
        Settings.llm = llm

        vector_store = DjangoAnnotationVectorStore.from_params(
            document_id=document.id, must_have_text=datacell.column.must_contain_text
        )
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

        # search_text
        search_text = datacell.column.match_text

        # query
        query = datacell.column.query

        # Special character
        if "|||" in search_text:

            logger.info(f"Detected special break character in examples `|||` - splitting and averaging embeddings.")

            examples = search_text.split('|||')
            embeddings: list[list[float | int]] = []
            for example in examples:
                vector = calculate_embedding_for_text(example)
                if vector is not None:
                    embeddings.append(calculate_embedding_for_text(example))

            # print(f"Calculate mean for embeddings {embeddings}")

            avg_embedding: np.ndarray = np.mean(embeddings, axis=0)
            print(f"Calculated avg embeddings: {type(avg_embedding)}")

            # print(f"Averaged embeddings: {avg_embedding}")

            queryset = (Annotation.objects.
            filter(document_id=document.id).
            order_by(
                CosineDistance("embedding", avg_embedding.tolist())
            )
            .annotate(
                similarity=CosineDistance("embedding", avg_embedding.tolist())
            ))[:similarity_top_k]
            print(f"Annotated queryset: {queryset}")

            nodes = [
                NodeWithScore(
                    node=Node(
                        doc_id=str(row.id),
                        text=row.raw_text,
                        embedding=row.embedding.tolist()
                        if getattr(row, "embedding", None) is not None
                        else [],
                        extra_info={
                            "page": row.page,
                            "bounding_box": row.bounding_box,
                            "annotation_id": row.id,
                            "label": row.annotation_label.text
                            if row.annotation_label
                            else None,
                            "label_id": row.annotation_label.id
                            if row.annotation_label
                            else None,
                        },
                    ),
                    score=row.similarity
                ) for row in queryset
            ]
            print(f"{len(nodes)} Nodes for reranker: {nodes}")

            # reranker = LLMRerank(
            #     choice_batch_size=5,
            #     top_n=3,
            # )
            sbert_rerank = SentenceTransformerRerank(
                model="cross-encoder/ms-marco-MiniLM-L-2-v2", top_n=5
            )
            retrieved_nodes = sbert_rerank.postprocess_nodes(
                nodes, QueryBundle(query)
            )
            print(f"{len(retrieved_nodes)} Reranked nodes")

            annotation_ids = [n.node.extra_info['annotation_id'] for n in retrieved_nodes]
            print(f"Annotation ids for reranked nodes: {annotation_ids}")

            datacell.sources.add(*annotation_ids)

            print(f"Resolved queryset: {queryset}")

            retrieved_text = "\n".join(
                [f"```Relevant Section:\n\n{node.text}\n```" for node in retrieved_nodes]
            )

        else:
            retriever = index.as_retriever(similarity_top_k=similarity_top_k)

            results = retriever.retrieve(search_text if search_text else query)

            sbert_rerank = SentenceTransformerRerank(
                model="cross-encoder/ms-marco-MiniLM-L-2-v2", top_n=5
            )
            retrieved_nodes = sbert_rerank.postprocess_nodes(
                results, QueryBundle(query)
            )

            for r in retrieved_nodes:
                print(f"Result: {r.node.extra_info}:\n{r}")

            retrieved_annotation_ids = [n.node.extra_info["annotation_id"] for n in retrieved_nodes]
            print(f"retrieved_annotation_ids: {retrieved_annotation_ids}")
            datacell.sources.add(*retrieved_annotation_ids)

            retrieved_text = "\n".join(
                [f"```Relevant Section:\n\n{n.text}\n```" for n in results]
            )

        logger.info(f"Retrieved text: {retrieved_text}")

        output_type = parse_model_or_primitive(datacell.column.output_type)
        logger.info(f"Output type: {output_type}")

        parse_instructions = datacell.column.instructions

        # TODO - eventually this can just be pulled from a separate Django vector index where we filter to definitions!
        definitions = ""
        if datacell.column.agentic:
            import nest_asyncio

            nest_asyncio.apply()

            engine = index.as_query_engine(similarity_top_k=similarity_top_k)

            query_engine_tools = [
                QueryEngineTool.from_defaults(
                    query_engine=engine,
                    name="document_parts",
                    description="Let's you use hybrid or vector search over this document to search for specific text "
                                "semantically or using text search.",
                )
            ]

            # create the function calling worker for reasoning
            worker = FunctionCallingAgentWorker.from_tools(
                query_engine_tools, verbose=True
            )

            # wrap the worker in the top-level planner
            agent = StructuredPlannerAgent(
                worker, tools=query_engine_tools, verbose=True
            )

            # TODO - eventually capture section hierarchy as nlm-sherpa does so we can query up a retrieved chunk to
            #  its parent section

            response = agent.query(
                f"""Please identify all of the defined terms - capitalized terms that are not well-known proper nouns,
                terms that in quotation marks or terms that are clearly definitions in the context of a given sentence,
                 such as blah blah, as used herein - the bros - and find their definitions. Likewise, if you see a
                 section reference, try to retrieve the original section text. You produce an output that looks like
                 this:
                ```

                ### Related sections and definitions ##########

                [defined term name]: definition
                ...

                [section name]: text
                ...

                ```

                Now, given the text to analyze below, please perform the analysis for this original text:
                ```
                {retrieved_text}
                ```
                """
            )
            definitions = str(response)

        retrieved_text = (
            f"Related Document:\n```\n{retrieved_text}\n```\n\n" + definitions
        )

        print(f"Resulting data for marvin: {retrieved_text}")

        if datacell.column.extract_is_list:
            print("Extract as list!")
            result = marvin.extract(
                retrieved_text, target=output_type, instructions=parse_instructions if parse_instructions else query
            )
        else:
            print("Extract single instance")
            result = marvin.cast(
                retrieved_text, target=output_type, instructions=parse_instructions if parse_instructions else query
            )

        print(f"Result processed from marvin: {result}")
        logger.debug(
            f"run_extract() - processing column datacell {datacell.id} for {datacell.document.id}"
        )

        if issubclass(output_type, BaseModel) or isinstance(output_type, BaseModel):
            datacell.data = {"data": result.model_dump()}
        elif output_type in [str, int, bool, float]:
            datacell.data = {"data": result}
        else:
            raise ValueError(f"Unsupported output type: {output_type}")
        datacell.completed = timezone.now()
        datacell.save()

    except Exception as e:
        logger.error(f"run_extract() - Ran into error: {e}")
        datacell.stacktrace = f"Error processing: {e}"
        datacell.failed = timezone.now()
        datacell.save()
