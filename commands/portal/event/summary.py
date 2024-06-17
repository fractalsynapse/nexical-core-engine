from systems.commands.index import Command


class Summary(Command('portal.event.summary')):

    def exec(self):
        self.data("Processing summary {} from {}".format(self.event_id, self.portal), self.event_fields)
        self.event_wrapper(self._perform_summary)

    def _perform_summary(self, event):
        if event.operation == 'delete':
            self.delete_summary(event, self.portal)
            self.send('agent:summarizer:delete', event.export())
            self.success("Successfully deleted summary: {}".format(event.id))
        else:
            summary = self.publish_summary(event, self.portal)
            self.send('agent:summarizer:summary', summary.export())
            self.success('Completed summary processing request successfully')
