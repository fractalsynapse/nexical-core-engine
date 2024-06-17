from systems.commands.index import Command
from utility.data import get_identifier


class Project(Command('portal.event.project')):

    def exec(self):
        self.data("Processing project update {} from {}".format(self.event_id, self.portal), self.event_fields)
        self.event_wrapper(self._update_project)

    def _update_project(self, event):
        if event.operation == 'delete':
            self._team_document_collection.filter(
                team__portal_name = self.portal,
                team__external_id = event.team_id,
                name__in = [
                    "note-{}".format(event.id),
                    "summary-{}".format(event.id)
                ]
            ).delete()

            self._team_project.filter(
                team__portal_name = self.portal,
                team__external_id = event.team_id,
                external_id = event.id
            ).delete()

            self.send('agent:projects:delete', event.export())
            self.success("Successfully deleted project: {}".format(event.id))
        else:
            documents = event.documents if event.documents else []

            team = self.save_instance(self._team, None, {
                'portal_name': self.portal,
                'external_id': event.team_id,
                'name': event.team_name
            })
            note_collection_name = "note-{}".format(event.id)
            note_collection = self.save_instance(self._team_document_collection, get_identifier(note_collection_name), {
                'team': team,
                'name': note_collection_name
            })
            summary_collection_name = "summary-{}".format(event.id)
            summary_collection = self.save_instance(self._team_document_collection, get_identifier(summary_collection_name), {
                'team': team,
                'name': summary_collection_name
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
                'team_document_collections': documents + [
                    note_collection.external_id,
                    summary_collection.external_id
                ]
            }, relation_key = True)

            self.send('agent:projects:update', event.export())
            self.success("Updated project: {}".format(event.id))
