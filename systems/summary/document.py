from .base import BaseModelSummarizer


class DocumentSummarizer(BaseModelSummarizer):

    def __init__(self, command, document_collection):
        super().__init__(
            command,
            document_collection,
            'team_document_collection',
            'team_document'
        )

        self.document_group_field = 'name'

        self.embedding_collection = 'team_document'
        self.embedding_id_field = 'collection_id'
        self.embedding_group_field = 'document_id'
