class PlanningManager:
    def __init__(self):
        self.plan = {}
    
    def update_plan(self, index, plan = None, mark = None):
        """
            update: Update the plan

            :param index: Index of plan to be updated
            :param plan: New plan to be updated; default None
            :param mark: New mark to be updated; default None
        """
        try:
            self.plan[index] = {
                "index": index,
                "plan": plan,
                "mark": mark
            }

            return f"Updated Plan: {str(self.plan[index])}"
        except Exception as e:
            return str(e)
        
    def delete_plan(self, index):
        """
            delete: Delete the plan
            
            :param index: Index of plan to be deleted
        """
        try:
            return "Deleted Plan: {str(self.plan.pop(index))}"
        except Exception as e:
            return str(e)
    
    def mark_plan(self, index):
        """
            mark: Mark a step as completed
            
            :param index: Index of plan to be marked
        """
        try:
            self.plan[index]['mark'] = True
            return f"Marked Plan: {str(self.plan[index])}"
        except Exception as e:
            return str(e)
    
    def create_plan(self, index, plan):
        """
            create: Create a new plan
            
            :param index: Index of plan to be created
            :param plan: New plan to be created
        """

        try:
            self.plan.update({
                index:{
                    "index":index,
                    "plan":plan,
                    "mark": False
                }
            })

            return f"Created Plan: {str(self.plan[index])}"
        except Exception as e:
            return str(e)