from systems.commands.index import Command
from systems.summary.document import DocumentSummarizer


class Documents(Command('model.summarize.documents')):

    def exec(self):
        summary = DocumentSummarizer(self, self.team_document_collection).generate(
            max_chunks = self.max_chunks,
            persona = self.persona.strip(),
            prompt = self.instruction.strip(),
            temperature = self.temperature,
            top_p = self.top_p,
            repetition_penalty = self.repetition_penalty
        )
        self.success(summary.text)
        summary.delete('text')
        self.data('Stats', summary.export())
