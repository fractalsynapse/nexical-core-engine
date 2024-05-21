from systems.commands.index import Command


class Recommendation(Command('recommendation')):

    def exec(self):
        self.data('Processing scanner', self.scanner.id)
        recommendations = self.generate_recommendations(self.scanner,
            focus_cutoff_score = self.focus_cutoff_score,
            focus_selectivity = self.focus_selectivity,
            focus_limit = self.focus_limit,
            search_cutoff_score = self.search_cutoff_score,
            search_selectivity = self.search_selectivity,
            search_limit = self.search_limit
        )
        self.success("Completed {} recommendation search with {} notices".format(
            self.scanner.id,
            len(recommendations)
        ))
