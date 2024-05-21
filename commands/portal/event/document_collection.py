from systems.commands.index import Command


class DocumentCollection(Command('portal.event.document_collection')):

    def exec(self):
        self.data("Processing document collection update {} from {}".format(self.event_id, self.portal), self.event_fields)
        self.event_wrapper(self._update_document_collection)

    def _update_document_collection(self, event):
        if event.operation == 'delete':
            self.delete_document_collection(event, self.portal)
            self.send('agent:documents:delete', event.export())
            self.success("Successfully deleted document collection: {}".format(event.document_collection_id))
        else:
            self.save_document_collection(event, self.portal)
            self.send('agent:documents:update', event.export())
            self.success("Updated document collection".format(event.document_collection_id))
