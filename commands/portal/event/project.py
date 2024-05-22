from systems.commands.index import Command


class Project(Command('portal.event.project')):

    def exec(self):
        self.data("Processing project update {} from {}".format(self.event_id, self.portal), self.event_fields)
        self.event_wrapper(self._update_project)

    def _update_project(self, event):
        if event.operation == 'delete':
            self._project.filter(
                portal_name = self.portal,
                external_id = event.id
            ).delete()

            self.send('agent:projects:delete', event.export())
            self.success("Successfully deleted project: {}".format(event.id))
        else:
            team = self.save_instance(self._team, None, {
                'portal_name': self.portal,
                'external_id': event.team_id,
                'name': event.team_name
            })
            self.save_instance(self._team_project, event.id, {
                'team': team,
                'name': event.name,
                'summary_model': event.summary_model,
                'summary_persona': event.summary_persona,
                'summary_format': event.format_prompt,
                'temperature': event.temperature,
                'top_p': event.top_p,
                'repetition_penalty': event.repetition_penalty,
                'team_document_collections': event.documents
            }, relation_key = True)

            self.send('agent:projects:update', event.export())
            self.success("Updated project: {}".format(event.id))
