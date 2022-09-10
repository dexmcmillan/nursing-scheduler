import pandas as pd
import numpy as np
import random
import math

class Schedule():
    
    staff = pd.read_csv("data/staff.csv")
    patients = pd.read_csv("data/patients.csv").set_index("patient_name")
    hours = list(range(0,23))
    
    
    
    def __init__(self):
        
        pass
    
    
    
    
    def daily_schedule(self):
        
        # Define the length of each nursing shift.
        SHIFT_LENGTH = 12
        
        # Define the maximum weight that nurses can have on their caseload at one time.
        MAX_LOAD = 15
        
        # Load in a table that will keep track of the weight assigned to each nurse for the day.
        daily_load_table = pd.DataFrame({"load": 0}, index=self.staff["name"].to_list())
        
        # Fill any empty values in the schedule (which should be all of them to start) with a "None" placeholder.
        self.patients = self.patients.fillna("None")
        
        # Loop through every patient in the patient list csv.
        for patient_name in self.patients.index.to_list():
            
            # Get the weight of the patient for calculating nurses workloads.
            patient_weight = self.patients.at[patient_name, "weight"]
            
            # Get a list of all nurses who are not yet at capacity for the day.
            nurses_left = daily_load_table.reset_index().loc[daily_load_table.reset_index()["load"] <= MAX_LOAD - patient_weight, "index"].to_list()
        
            # Loop through each hour in the schedule.
            for hour in self.hours:
                
                # Get the current patient we're looping through in the above loop.
                patient = self.patients.loc[[patient_name], :]
            
                # If there is a preferred nurse listed for this patient, prioritize them if they are available.
                preferred_nurse = self.patients.at[patient_name, "preferred_nurse"]
                
                if preferred_nurse != "None" and preferred_nurse in nurses_left:
                    assignee = preferred_nurse
                else:
                    assignee = daily_load_table.loc[daily_load_table.index.isin(nurses_left), ["load"]].sort_values("load").index[0]
                
                # If nobody is assigned for this patient for the specified hour, assign a nurse from the available nurses list.
                if patient.at[patient_name, str(hour)] == "None":
                    
                    # Increase load on the staff member who was assigned.
                    daily_load_table.at[assignee, "load"] = daily_load_table.at[assignee, "load"] + patient_weight
                    
                    # Remove the nurse from the eligible list so they are not assigned to the same patient for a double shift.
                    nurses_left.remove(assignee)
                    
                    # Fill out the next x hours, where x is the shift length specified.
                    for n in range(0,SHIFT_LENGTH):
                        
                        self.patients.at[patient_name, str(np.clip(int(hour)+n, self.hours[0], self.hours[-1]))] = assignee
                        
                        
        print(self.patients, daily_load_table)
        
        
schedule = Schedule().daily_schedule()