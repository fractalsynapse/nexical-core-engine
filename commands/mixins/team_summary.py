from bs4 import BeautifulSoup
from django.conf import settings

from systems.models.index import Model
from systems.commands.index import CommandMixin
from systems.summary.text import TextSummarizer
from systems.summary.document import DocumentSummarizer
from utility.data import Collection, get_identifier, ensure_list
from utility.topics import TopicModel

import time
import re


class TeamSummaryCommandMixin(CommandMixin("team_summary")):

    def publish_summary(self, event, portal_name):
        topic_parser = TopicModel()

        team = self._team.qs.get(portal_name=portal_name, external_id=event.team_id)
        project = self._team_project.retrieve(event.project_id, team=team)

        summary = self.generate_project_summary(
            project,
            event.prompt,
            use_default_format=event.use_default_format,
            output_format=event.format,
            output_endings=event.endings,
            max_sections=event.max_sections,
            sentence_limit=event.sentence_limit,
        )

        summary_text = BeautifulSoup(summary.text or "", "html.parser").get_text()
        document_collection = self.save_instance(
            self._team_document_collection,
            None,
            {
                "team": team,
                "external_id": get_identifier("summary-{}".format(event.project_id)),
                "name": "{} Research Summaries".format(project.name),
            },
        )
        document = self.save_instance(
            self._team_document,
            None,
            {
                "team_document_collection": document_collection,
                "external_id": event.id,
                "type": "summary",
                "name": (
                    event.name
                    if event.name
                    else (
                        (event.prompt[:250] + "...")
                        if len(event.prompt) > 250
                        else event.prompt
                    )
                ),
                "hash": get_identifier(summary_text),
                "text": summary_text,
                "sentences": (
                    self.parse_sentences(summary_text, validate=False)
                    if summary_text
                    else []
                ),
            },
        )
        if self._store_document_topics(document, topic_parser):
            if self.debug and self.verbosity > 2:
                self.data(
                    "Document {} topics".format(self.key_color(document.id)),
                    document.topics,
                )

        self._store_document_embeddings(document, topic_parser)

        self.portal_update(
            portal_name,
            "summary",
            id=event.id,
            summary=summary.text or "",
            token_count=summary.token_count or 0,
            processing_time=summary.processing_time or 0,
            processing_cost=summary.processing_cost or 0,
            processed_time=self.time.now,
            references=list(summary.documents.values()),
        )
        return summary

    def delete_summary(self, event, portal_name):
        team = self._team.qs.get(portal_name=portal_name, external_id=event.team_id)
        document_collection = self._team_document_collection.retrieve(
            get_identifier("summary-{}".format(event.project_id)), team=team
        )
        if document_collection:
            for document in self._team_document.filter(
                external_id=event.id, team_document_collection=document_collection
            ):
                self._remove_document_embeddings(document)
                document.delete()

    def generate_project_summary(
        self,
        project,
        prompt,
        use_default_format=True,
        output_format="",
        output_endings=[],
        max_sections=10,
        sentence_limit=100,
    ):
        start_time = time.time()

        documents = self._get_summary_documents(project)
        included_documents = {}

        config = {
            "persona": project.summary_persona,
            "temperature": project.temperature,
            "top_p": project.top_p,
            "repetition_penalty": project.repetition_penalty,
        }

        if use_default_format:
            output_format = "{}. {}".format(
                project.summary_format.removesuffix("."),
                output_format.removesuffix("."),
            )

        if self.debug and self.verbosity > 2:
            self.info("======================")
            self.data("Team", project.team)
            self.data("Project", project)
            self.data("Output Format", output_format)
            self.data("Summary Documents", documents)

        topic_summary = self._summarize_topic(
            project,
            prompt,
            documents,
            max_sections,
            sentence_limit,
            config,
        )
        for summary in topic_summary.summaries:
            for identifier, document_info in summary.documents.items():
                score = document_info["score"]
                document = document_info["document"]

                included_documents[identifier] = {
                    "score": float(score),
                    "type": document.type,
                    "document_id": document.external_id,
                }

        topic_texts = [summary.text.strip() for summary in topic_summary.summaries]
        if not topic_texts and documents and len(documents) > 2:
            topic_texts = None

        if self.debug and self.verbosity > 2:
            self.data("Summary Topic Text", topic_texts)
            self.data("Summary Included Documents", included_documents)

        summary = TextSummarizer(
            self, topic_texts, provider=project.summary_model
        ).generate(
            prompt, output_format=output_format, output_endings=output_endings, **config
        )

        summary.request_tokens += topic_summary.request_tokens
        summary.response_tokens += topic_summary.response_tokens
        summary.processing_cost += topic_summary.processing_cost
        summary.processing_time = time.time() - start_time
        summary.documents = included_documents
        return summary

    def _summarize_topic(
        self,
        project,
        user_prompt,
        instances,
        max_sections,
        sentence_limit,
        config,
    ):
        instances = ensure_list(instances) if instances else []
        request_tokens = 0
        response_tokens = 0
        processing_cost = 0
        documents = {}
        summaries = []

        model = (
            project.summary_prompt_model
            if project.summary_prompt_model
            else project.summary_model
        )

        if instances:
            topic_prompt = "Summarize the document text for inclusion into a higher level summary on the topic."
            summary_results = self.run_list(
                instances,
                self._summarize_documents,
                project,
                topic_prompt,
                user_prompt,
                max_sections,
                sentence_limit,
                config,
            )
            for summary in summary_results.data:
                if summary.result:
                    request_tokens += summary.result.request_tokens
                    response_tokens += summary.result.response_tokens
                    processing_cost += summary.result.processing_cost
                    documents = {**documents, **summary.result.documents}
                    summaries.append(summary.result)

        return Collection(
            summaries=summaries,
            request_tokens=request_tokens,
            response_tokens=response_tokens,
            processing_cost=processing_cost,
            documents=documents,
        )

    def _summarize_documents(
        self,
        collection_id,
        project,
        prompt,
        user_prompt,
        max_sections,
        sentence_limit,
        config,
    ):
        document_collection = Model("team_document_collection").facade.retrieve_by_id(
            collection_id
        )
        if document_collection:
            model = (
                project.summary_topic_model
                if project.summary_topic_model
                else project.summary_model
            )
            summary = DocumentSummarizer(
                self, document_collection, provider=model
            ).generate(
                prompt,
                user_prompt=user_prompt,
                max_chunks=max_sections,
                sentence_limit=sentence_limit,
                **config
            )
            if summary.text:
                summary.text = """
The following is information from the document collection '{}'{}

Use the following information for summarization and answering questions:

{}
""".format(
                    document_collection.name,
                    (
                        " with the description: {}.".format(
                            document_collection.description.strip(".!?")
                        )
                        if document_collection.description
                        else "."
                    ),
                    summary.text,
                )
            return summary
        return None

    def _get_summary_documents(self, project):
        def _get_documents(inner_project, processed_ids):
            documents = list(
                inner_project.team_document_collections.values_list("id", flat=True)
            )
            for sub_project in inner_project.team_projects.all():
                if sub_project.id not in processed_ids:
                    processed_ids.append(sub_project.id)
                    documents.extend(_get_documents(sub_project, processed_ids))
            return documents

        return list(set(_get_documents(project, [])))
