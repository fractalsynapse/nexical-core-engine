from bs4 import BeautifulSoup
from django.conf import settings

from systems.models.index import Model
from systems.commands.index import CommandMixin
from systems.summary.text import TextSummarizer
from systems.summary.document import DocumentSummarizer
from utility.data import Collection, get_identifier, ensure_list
from utility.topics import TopicModel

import time


class TeamSummaryCommandMixin(CommandMixin('team_summary')):

    def publish_summary(self, event, portal_name):
        topic_parser = TopicModel()
        team = self._team.qs.get(portal_name = portal_name, external_id = event.team_id)
        project = self._team_project.retrieve(event.project_id, team = team)

        if event.use_default_format:
            output_format = "{}. {}.".format(project.summary_format.removesuffix('.'), event.format.removesuffix('.'))
        else:
            output_format = event.format

        summary = self._generate_summary(project.summary_model,
            prompt = event.prompt,
            output_format = output_format,
            output_endings = event.endings,
            documents = self._get_summary_documents(project),
            persona = project.summary_persona,
            temperature = project.temperature,
            top_p = project.top_p,
            repetition_penalty = project.repetition_penalty,
            max_chunks = event.max_sections,
            sentence_limit = event.sentence_limit
        )

        summary_text = BeautifulSoup(summary.text or '', 'html.parser').get_text()
        document_collection = self.save_instance(self._team_document_collection, None, {
            'team': team,
            'external_id': get_identifier("summary-{}".format(event.project_id)),
            'name': "{} Research Summaries".format(project.name)
        })
        document = self.save_instance(self._team_document, None, {
            'team_document_collection': document_collection,
            'external_id': event.id,
            'type': 'summary',
            'name': event.name if event.name else ((event.prompt[:250] + '...') if len(event.prompt) > 250 else event.prompt),
            'hash': get_identifier(summary_text),
            'text': summary_text,
            'sentences': self.parse_sentences(summary_text, validate = False) if summary_text else []
        })
        if self._store_document_topics(document, topic_parser):
            self.data("Document {} topics".format(self.key_color(document.id)), document.topics)

        self._store_document_embeddings(document, topic_parser)

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


    def delete_summary(self, event, portal_name):
        team = self._team.qs.get(portal_name = portal_name, external_id = event.team_id)
        document_collection = self._team_document_collection.retrieve(
            get_identifier("summary-{}".format(event.project_id)),
            team = team
        )
        if document_collection:
            self._team_document.filter(
                external_id = event.id,
                team_document_collection = document_collection
            ).delete()


    def _get_summary_documents(self, project):
        def _get_documents(inner_project, processed_ids):
            documents = list(inner_project.team_document_collections.values_list('id', flat = True))
            for sub_project in inner_project.team_projects.all():
                if sub_project.id not in processed_ids:
                    processed_ids.append(sub_project.id)
                    documents.extend(_get_documents(sub_project, processed_ids))
            return documents
        return list(set(_get_documents(project, [])))


    def _generate_summary(self, model, prompt, output_format = '', output_endings = None, documents = None, **config):
        start_time = time.time()
        max_chunks = config.pop('max_chunks', 10)
        sentence_limit = config.pop('sentence_limit', 50)
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
                model,
                prompt,
                topic_info['prompt'],
                topic_info['instances'],
                topic_info['method'],
                max_chunks,
                sentence_limit,
                config
            )

        topic_results = self.run_list(topics, summarize_topic)
        for topic in topic_results.data:
            request_tokens += topic.result.request_tokens
            response_tokens += topic.result.response_tokens

            for summary in topic.result.summaries:
                for identifier, document_info in summary.documents.items():
                    score = document_info['score']
                    document = document_info['document']

                    included_documents[identifier] = {
                        'score': float(score),
                        'type': document.type,
                        'document_id': document.external_id
                    }
            summaries.extend(topic.result.summaries)

        topic_text = "\n\n\n".join([ summary.text for summary in summaries ]).strip() if summaries else ''
        if not topic_text and documents and len(documents) > 2:
            topic_text = None

        summary = TextSummarizer(self, topic_text, provider = model).generate(
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


    def _summarize_topic(self, model, user_prompt, detail_prompt, instances, summarize_method, max_chunks, sentence_limit, config):
        instances = ensure_list(instances) if instances else []
        request_tokens = 0
        response_tokens = 0
        documents = {}
        summaries = []

        if instances:
            research_prompt = TextSummarizer(self, user_prompt, provider = model).generate(detail_prompt, **config)
            request_tokens += research_prompt.request_tokens
            response_tokens += research_prompt.response_tokens

            summary_results = self.run_list(
                instances,
                summarize_method,
                model,
                research_prompt.text,
                user_prompt,
                max_chunks,
                sentence_limit,
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


    def _summarize_documents(self, collection_id, model, prompt, user_prompt, max_chunks, sentence_limit, config):
        document_collection = Model('team_document_collection').facade.retrieve_by_id(collection_id)
        if document_collection:
            summary = DocumentSummarizer(self, document_collection, provider = model).generate(
                prompt,
                user_prompt = user_prompt,
                max_chunks = max_chunks,
                sentence_limit = sentence_limit,
                **config
            )
            if summary.text:
                summary.text = """
The following is information from the document collection '{}'{}

Use this information exclusively for summarization and answering questions:

{}
""".format(
                    document_collection.name,
                    " with the description: {}.".format(document_collection.description.strip('.!?')) if document_collection.description else '.',
                    summary.text
                )
            return summary
        return None
