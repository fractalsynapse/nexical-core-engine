from systems.commands.index import Command
from utility.data import get_identifier


class Project(Command("portal.event.project")):

    def exec(self):
        self.data(
            "Processing project update {} from {}".format(self.event_id, self.portal),
            self.event_fields,
        )
        self.event_wrapper(self._update_project)

    def _update_project(self, event):
        if event.operation == "delete":
            self._team_document_collection.filter(
                team__portal_name=self.portal,
                team__external_id=event.team_id,
                name__in=["note-{}".format(event.id), "summary-{}".format(event.id)],
            ).delete()

            self._team_project.filter(
                team__portal_name=self.portal,
                team__external_id=event.team_id,
                external_id=event.id,
            ).delete()

            self.send("agent:projects:delete", event.export())
            self.success("Successfully deleted project: {}".format(event.id))
        else:
            documents = event.documents if event.documents else []
            projects = event.projects if event.projects else []
            access_teams = event.access_teams if event.access_teams else []

            team = self.save_instance(
                self._team,
                None,
                {
                    "portal_name": self.portal,
                    "external_id": event.team_id,
                    "name": event.team_name,
                },
            )
            note_collection_name = "note-{}".format(event.id)
            note_collection = self.save_instance(
                self._team_document_collection,
                get_identifier(note_collection_name),
                {"team": team, "name": note_collection_name},
            )
            summary_collection_name = "summary-{}".format(event.id)
            summary_collection = self.save_instance(
                self._team_document_collection,
                get_identifier(summary_collection_name),
                {"team": team, "name": summary_collection_name},
            )

            instance = self.save_instance(
                self._team_project,
                event.id,
                {
                    "team": team,
                    "name": event.name,
                    "summary_model": event.summary_model,
                    "summary_topic_model": event.summary_topic_model,
                    "summary_prompt_model": event.summary_prompt_model,
                    "summary_persona": event.summary_persona,
                    "summary_format": event.format_prompt,
                    "temperature": event.temperature,
                    "top_p": event.top_p,
                    "repetition_penalty": event.repetition_penalty,
                    "team_document_collections": [
                        note_collection.external_id,
                        summary_collection.external_id,
                    ],
                    "team_projects": None,
                    "access_teams": access_teams,
                },
                relation_key=True,
            )

            for document_collection in self.facade(
                "team_document_collection", False
            ).filter(external_id__in=documents):
                instance.team_document_collections.add(document_collection)
                self.success(
                    "Successfully added document collection: {}".format(
                        document_collection.id
                    )
                )

            for project in self.facade("team_project", False).filter(
                external_id__in=projects
            ):
                instance.team_projects.add(project)
                self.success("Successfully added project: {}".format(project.id))

            self.send("agent:projects:update", event.export())
            self.success("Updated project: {}".format(event.id))
