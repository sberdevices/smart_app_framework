from smart_kit.models.dialogue_manager import DialogueManager


class CustomDialogueManager(DialogueManager):

    """
        В собственном DialogManager можно переопределить логику, связанную с вызовом сценариев по входяшему интенту
    """
    
    def __init__(self, scenario_descriptions, app_name, **kwargs):
        super(CustomDialogueManager, self).__init__(scenario_descriptions, app_name, **kwargs)