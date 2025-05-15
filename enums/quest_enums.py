from enum import Enum

class QuestStatus(str, Enum):

    NOT_STARTED = "not_started"  
    IN_PROGRESS = "in_progress"  
    COMPLETED = "completed"    
    FAILED = "failed"        

    def __str__(self):
        return self.value

class QuestType(str, Enum):

    MAIN = "main"            
    SIDE = "side"            
    OPTIONAL = "optional"      
    REPEATABLE = "repeatable"  
    TIMED = "timed"          

    def __str__(self):
        return self.value