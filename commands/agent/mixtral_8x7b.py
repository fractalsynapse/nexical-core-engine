from systems.commands.index import Agent


class Mixtral8x7b(Agent('model.mixtral_8x7b')):

    def exec(self):
        self.exec_summary(
            'mixtral_di_7bx8',
            'agent:model:mixtral_8x7b'
        )
