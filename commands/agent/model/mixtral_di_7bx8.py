from systems.commands.index import Agent


class MixtralDi7Bx8(Agent('model.mixtral_di_7bx8')):

    def exec(self):
        self.exec_summary('mixtral_di_7bx8')
