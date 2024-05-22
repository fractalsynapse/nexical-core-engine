from django.conf import settings

from systems.models.index import Model
from systems.commands.index import CommandMixin
from systems.summary.text import TextSummarizer
from systems.summary.document import DocumentSummarizer
from utility.data import Collection, get_identifier, ensure_list

import time


class TeamSummaryCommandMixin(CommandMixin('team_summary')):

    def publish_summary(self, event, portal_name):
        project = self._team_project.retrieve(event.project_id, team_id = event.team_id)
        documents = list(self._team_document_collection.filter(external_id__in = event.documents).values_list('id', flat=True))

        summary = self.perform_summary(event.prompt,
            model = project.summary_model,
            output_format = project.summary_format,
            output_endings = event.endings,
            documents = documents,
            persona = project.summary_persona,
            temperature = project.temperature,
            top_p = project.top_p,
            repetition_penalty = project.repetition_penalty
        )
        self.portal_update(portal_name,
            'summary',
            id = event.id,
            summary = summary.text or '',
            token_count = summary.token_count or 0,
            processing_time = summary.processing_time or 0,
            processing_cost = summary.processing_cost or 0,
            processed_time = self.time.now,
            references = list(summary.documents.values())
        )
        return summary


    def perform_summary(self, prompt, output_format = '', output_endings = None, documents = None, **config):
        start_time = time.time()
        max_chunks = config.pop('max_chunks', 10)
        request_tokens = 0
        response_tokens = 0
        included_documents = {}
        summaries = []

        topics = [
            {
                'prompt': """
Generate a detailed prompt to summarize a collection of documents
that may or may not have information pertaining to the
question in the text excerpt.
Include only the prompt in the response.
""".strip(),
                'instances': documents,
                'method': self._summarize_documents
            }
        ]

        def summarize_topic(topic_info):
            return self._summarize_topic(
                prompt,
                topic_info['prompt'],
                topic_info['instances'],
                topic_info['method'],
                max_chunks,
                config
            )

        topic_results = self.run_list(topics, summarize_topic)
        for topic in topic_results.data:
            request_tokens += topic.result.request_tokens
            response_tokens += topic.result.response_tokens

            for summary in topic.result.summaries:
                for identifier, document in summary.documents.items():
                    included_documents[identifier] = {
                        'score': float(identifier.split(':')[0]),
                        'type': document.facade.meta.data_name,
                        'document_id': document.external_id if document.facade.meta.data_name == 'team_document' else document.id
                    }
            summaries.extend(topic.result.summaries)

        topic_text = "\n\n\n".join([ summary.text for summary in summaries ]) if summaries else ''
        summary = TextSummarizer(self, topic_text).generate(
            prompt,
            output_format = output_format,
            output_endings = output_endings,
            **config
        )
        summary.request_tokens += request_tokens
        summary.response_tokens += response_tokens
        summary.token_count = (summary.request_tokens + summary.response_tokens)
        summary.processing_time = (time.time() - start_time)
        summary.processing_cost = (summary.token_count * settings.SUMMARIZER_COST_PER_TOKEN)
        summary.documents = included_documents
        return summary


    def _summarize_topic(self, user_prompt, detail_prompt, instances, summarize_method, max_chunks, config):
        instances = ensure_list(instances) if instances else []
        request_tokens = 0
        response_tokens = 0
        documents = {}
        summaries = []

        if instances:
            research_prompt = TextSummarizer(self, user_prompt).generate(detail_prompt, **config)
            request_tokens += research_prompt.request_tokens
            response_tokens += research_prompt.response_tokens

            summary_results = self.run_list(
                instances,
                summarize_method,
                research_prompt.text,
                max_chunks,
                config
            )
            for summary in summary_results.data:
                if summary.result:
                    request_tokens += summary.result.request_tokens
                    response_tokens += summary.result.response_tokens
                    documents = { **documents, **summary.result.documents }
                    summaries.append(summary.result)

        return Collection(
            summaries = summaries,
            request_tokens = request_tokens,
            response_tokens = response_tokens,
            documents = documents
        )


    def _summarize_documents(self, collection_id, prompt, max_chunks, config):
        document_collection = Model('team_document_collection').facade.retrieve_by_id(collection_id)
        if document_collection:
            summary = DocumentSummarizer(self, document_collection).generate(
                prompt,
                max_chunks = max_chunks,
                **config
            )
            summary.text = """
The following is a description of the document collection: {}

{}
""".format(
                document_collection.name,
                summary.text
            )
            return summary
        return None
