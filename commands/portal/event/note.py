from systems.commands.index import Command


class Note(Command('portal.event.note')):

    def exec(self):
        self.data("Processing note update {} from {}".format(self.event_id, self.portal), self.event_fields)
        self.event_wrapper(self._update_note)

    def _update_note(self, event):
        if event.operation == 'delete':
            self.delete_note(event, self.portal)
            self.send('agent:notes:delete', event.export())
            self.success("Successfully deleted note: {}".format(event.id))
        else:
            self.save_note(event, self.portal)
            self.send('agent:notes:update', event.export())
            self.success("Updated note".format(event.id))
