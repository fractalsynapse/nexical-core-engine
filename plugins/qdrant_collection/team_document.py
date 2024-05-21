from systems.plugins.index import BaseProvider


class Provider(BaseProvider('qdrant_collection', 'team_document')):

    def _get_index_fields(self):
        return {
            'team_id': 'keyword',
            'collection_id': 'keyword',
            'document_id': 'keyword',
            'topics': 'keyword',
            'order': 'float'
        }

    def _get_document_id_filters(self, team_id = None, collection_id = None, document_id = None):
        from qdrant_client import models

        filters = []

        if team_id:
            filters.append(self._get_query_id_condition('team_id', team_id))
        if collection_id:
            filters.append(self._get_query_id_condition('collection_id', collection_id))
        if document_id:
            filters.append(self._get_query_id_condition('document_id', document_id))

        return models.Filter(must = filters) if filters else None


    def count(self, team_id = None, collection_id = None, document_id = None):
        return self._get_count_query(
            self._get_document_id_filters(team_id, collection_id, document_id)
        )

    def exists(self, team_id = None, collection_id = None, document_id = None):
        return self._check_exists(
            self._get_document_id_filters(team_id, collection_id, document_id)
        )

    def get(self, team_id = None, collection_id = None, document_id = None, fields = None, include_vectors = False):
        return self._run_query(
            self._get_document_id_filters(team_id, collection_id, document_id),
            fields = fields,
            include_vectors = include_vectors
        )

    def store(self, team_id, collection_id, document_id, sentence, embedding, topics, order):
        return self.request_upsert(
            collection_name = self.name,
            points = [
                self._get_record(sentence, embedding,
                    team_id = team_id,
                    collection_id = collection_id,
                    document_id = document_id,
                    topics = topics,
                    order = order
                )
            ]
        )

    def remove(self, team_id = None, collection_id = None, document_id = None):
        return self.request_delete(
            collection_name = self.name,
            points_selector = self._get_document_id_filters(team_id, collection_id, document_id)
        )
