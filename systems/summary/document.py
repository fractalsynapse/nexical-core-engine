from .base import BaseModelSummarizer


class DocumentSummarizer(BaseModelSummarizer):

    def __init__(self, command, document_collection, provider = None):
        super().__init__(
            command,
            document_collection,
            text_facade = 'team_document_collection',
            document_facade = 'team_document',
            provider = provider
        )
        self.document_id_field = 'team_document_collection_id'
        self.document_group_field = 'name'

        self.embedding_collection = 'team_document'
        self.embedding_id_field = 'collection_id'
