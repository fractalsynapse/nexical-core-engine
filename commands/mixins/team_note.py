from systems.commands.index import CommandMixin
from utility.data import get_identifier
from utility.topics import TopicModel


class TeamNoteCommandMixin(CommandMixin('team_note')):

    def save_note(self, event, portal_name):
        topic_parser = TopicModel()
        team = self._team.qs.get(portal_name = portal_name, external_id = event.team_id)
        project = self._team_project.retrieve(event.project_id, team = team)

        document_collection = self.save_instance(self._team_document_collection, None, {
            'team': team,
            'external_id': get_identifier("note-{}".format(event.project_id)),
            'name': "{} Notes".format(project.name)
        })
        document = self.save_instance(self._team_document, None, {
            'team_document_collection': document_collection,
            'external_id': event.id,
            'type': 'note',
            'name': event.name,
            'hash': get_identifier(event.message),
            'text': event.message,
            'sentences': self.parse_sentences(event.message, validate = False) if event.message else []
        })
        if self._store_document_topics(document, topic_parser):
            self.data("Document {} topics".format(self.key_color(document.id)), document.topics)

        self._store_document_embeddings(document, topic_parser)

    def delete_note(self, event, portal_name):
        team = self._team.qs.get(portal_name = portal_name, external_id = event.team_id)
        document_collection = self._team_document_collection.retrieve(
            get_identifier("note-{}".format(event.project_id)),
            team = team
        )
        if document_collection:
            self._team_document.filter(
                external_id = event.id,
                team_document_collection = document_collection
            ).delete()
