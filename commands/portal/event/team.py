from systems.commands.index import Command


class Team(Command('portal.event.team')):

    def exec(self):
        self.data("Processing team update {} from {}".format(self.event_id, self.portal), self.event_fields)
        self.event_wrapper(self._update_team)

    def _update_team(self, event):
        if event.operation == 'delete':
            self._team.filter(
                portal_name = self.portal,
                external_id = event.id
            ).delete()

            self.send('agent:teams:delete', event.export())
            self.success("Successfully deleted team: {}".format(event.id))
