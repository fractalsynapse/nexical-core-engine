from systems.commands.index import CommandMixin
from utility.data import get_identifier
from utility.topics import TopicModel


class TeamDocumentCollectorCommandMixin(CommandMixin('team_document_collector')):

    def save_document_collection(self, event, portal_name):
        topic_parser = TopicModel()
        team = self._team.qs.get(portal_name = portal_name, external_id = event.team_id)
        document_collection = self.save_instance(self._team_document_collection, None, {
            'team': team,
            'external_id': event.id,
            'name': event.name
        })
        document_index = {}

        for document_hash in document_collection.team_document.values_list('hash', flat = True):
            document_index[document_hash] = True

        def save_document(file_info):
            document_index.pop(file_info['hash'], None)

            document = self._team_document.filter(
                team_document_collection = document_collection,
                hash = file_info['hash']
            )
            if not document:
                text = self.parse_file_text(portal_name, 'document', file_info['id'])
                document = self.save_instance(self._team_document, None, {
                    'team_document_collection_id': document_collection.id,
                    'external_id': file_info['id'],
                    'type': 'file',
                    'name': file_info['name'],
                    'hash': file_info['hash'],
                    'text': text,
                    'sentences': self.parse_sentences(text, validate = False) if text else []
                })
                if self._store_document_topics(document, topic_parser):
                    self.data("Document {} topics".format(self.key_color(document.id)), document.topics)

                self._store_document_embeddings(document, topic_parser)

        self.run_list(event.get('files', []), save_document)
        if document_index:
            for document in self._team_document.filter(
                team_document_collection = document_collection,
                hash__in = list(document_index.keys())
            ):
                self._remove_document_embeddings(document)
                document.delete()

        self._publish_document_update_time(event, portal_name)
        return document_collection

    def delete_document_collection(self, event, portal_name):
        for collection in self._team_document_collection.filter(
            team__portal_name = portal_name,
            team__external_id = event.team_id,
            external_id = event.id
        ):
            for document in collection.team_document.all():
                self._remove_document_embeddings(document)
            collection.delete()


    def _store_document_embeddings(self, document, topic_parser):
        qdrant = self.qdrant('team_document')
        self._remove_document_embeddings(document)

        if document.text:
            data = self.generate_text_embeddings(document.text)
            if data:
                for sentence_index, sentence in enumerate(data.sentences):
                    qdrant.store(
                        document.team_document_collection.team.id,
                        document.team_document_collection.id,
                        document.id,
                        sentence,
                        data.embeddings[sentence_index],
                        topic_parser.parse(sentence),
                        float(sentence_index)
                    )

    def _remove_document_embeddings(self, document):
        qdrant = self.qdrant('team_document')
        qdrant.remove(
            document_id = document.id
        )


    def _store_document_topics(self, document, topic_parser):
        if (not document.topics) and document.sentences:
            document.topics = topic_parser.get_index(*document.sentences)
            document.save()
            return True
        return False


    def _publish_document_update_time(self, event, portal_name):
        self.portal_update(portal_name,
            'library',
            id = event.id,
            processed_time = self.time.now
        )
