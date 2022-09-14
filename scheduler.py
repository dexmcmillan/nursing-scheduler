import pandas as pd
import numpy as np
import warnings
import logging
        
# Turn on logging of INFO level.
logging.basicConfig(level=logging.INFO)

# Filter out annoying deprecation warnings.
warnings.simplefilter(action='ignore', category=FutureWarning)







# This error is thrown when there are not enough staff left while the schedule is created.
class NotEnoughStaff(Exception):    
    def __init__(self):
        super().__init__(f"Not enough staff!")

# This error is thrown when a preferred nurse is specified for a patient that is not in the staff list.
class NoNurseByThatNameError(Exception):    
    def __init__(self):
        super().__init__(f"No nurse employed by that name. Please check that the spelling of the preferred nurse precisely matches their name on the staff list.")







class Schedule():
    
    # The size (in minutes) of the blocks in the schedule.
    block_size_minutes = 60
    
    # A list of hours in the day.
    hours = pd.date_range("2022-09-12 00:00", "2022-09-17 23:30", freq=f"{block_size_minutes}min")
    
    # A staff list pulled from an external CSV.
    staff = pd.read_csv("data/staff.csv")
    
    # A list of nurses available in the current week.
    weekly_list = pd.DataFrame()
    
    # A list of nurses available in the current day.
    daily_list = pd.DataFrame()
    
    # A list of patients that need nursing care.
    # Add columns on with labels 0-23 to represent their daily schedule.
    patients = pd.read_csv("data/patients.csv").set_index("patient_name")
    
    # This is the property where the dataframe representing the final schedule will be stored.
    schedule = pd.DataFrame()
    
    
    
    
    
    
    def __init__(self):
        
        self.schedule = self.schedule.append(pd.DataFrame(columns=self.patients.index.to_list(), index=self.hours))
        
        # Load in a table that will keep track of the weight assigned to each nurse for the day.
        self.staff[["load", "hours_this_week", "patients"]] = 0
        self.staff = self.staff.set_index("name")
        
        self.weekly_list = self.staff.copy()
        self.daily_list = self.staff.copy()
    
    


              
    
    
    
    
    # This function chooses a nurse from the nurses available that day, week.
    def _choose_nurse(self):
        
        # Find all potential assigned_nurses who are tied with the lowest patient load.
        lowest_load = (self.daily_list
                    .sort_values(["hours_this_week", "load"])
                    .iat[0,self.daily_list.columns.get_loc("load")]
                    )
        
        nurses_to_choose_from = self.daily_list.loc[(self.daily_list["load"] == lowest_load) & (self.weekly_list["hours_this_week"] < (self.weekly_list["weekly_hours"] + self.weekly_list["shift_length"])), :]
        
        if len(nurses_to_choose_from) < 1:
            raise NotEnoughStaff()
        
        # Randomize them and pick one from those who are tied.
        return nurses_to_choose_from.sample(frac=1).index[0]
    
    
    
    
    
    
    
    def daily_schedule(self):
        # Build out a skeleton schedule in the schedule property, which will eventually be filled out and exported.
        self.schedule = (pd.DataFrame(columns=self.patients.index.to_list(), index=self.hours))
        
        # Get a list of days defined in the skeleton schedule.
        days = list(dict.fromkeys([x.strftime("%Y-%m-%d") for x in self.schedule.index]))
        
        logging.info(f"Nurses left THIS WEEK: {len(self.weekly_list)}")
                
        # Loop through each day in the schedule.
        for day in days:
            
            logging.info(f"Assigning nurses for {day}.")
            
            # Every day, reset the load table so it can be recalcuated (it is done by day).
            self.weekly_list.loc[:, "load"] = 0
            
            # Loop through every patient in the patient list csv.
            for patient_name in self.schedule.columns.to_list():
                    
                # If there is a preferred nurse listed for this patient, prioritize them if they are available.
                preferred_nurse = self.patients.at[patient_name, "preferred_nurse"]
                
                if preferred_nurse not in self.staff.index.to_list() and preferred_nurse is not np.nan:
                    raise NoNurseByThatNameError()
                else: pass
                
                # Get the weight of the patient for calculating nurses workloads.
                patient_weight = self.patients.at[patient_name, "weight"]
                
                # We loop through each day's hours separately. Get them here.
                daily_hours = (self.schedule
                    .reset_index()
                    .loc[self.schedule.index.strftime("%Y-%m-%d") == day, "index"]
                    .apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
                    .to_list()
                    )
                
                # Loop through each hour in the schedule.
                for hour in daily_hours:
                    
                    # If nobody is assigned for this patient for the specified hour, assign a nurse from the available nurses list.
                    if self.schedule.at[hour, patient_name] is np.nan:
                        
                        # Check if this patient has a preferred nurse listed.
                        if preferred_nurse in self.daily_list.index.to_list() and preferred_nurse in self.weekly_list.index.to_list():
                            
                            assigned_nurse = preferred_nurse
                            
                        else: assigned_nurse = self._choose_nurse()
                        
                        # Assign the nurse to the empty schedule slot.
                        self.schedule.at[hour, patient_name] = assigned_nurse
                        
                        # Get the value corresponding to the nurse's preferred shift length from the staff table.
                        assigned_nurse_shift_length = self.weekly_list.at[assigned_nurse, "shift_length"]
                        
                        # Carry forward their name for the number of blocks equal to their desired shift length.
                        self.schedule[patient_name] = (self.schedule[patient_name]
                                                       .fillna(method="ffill", limit=int(assigned_nurse_shift_length*(60/self.block_size_minutes)))
                                                       )
                        
                        # Increase load on the staff member who was assigned.
                        self.daily_list.at[assigned_nurse, "load"] = self.daily_list.at[assigned_nurse, "load"] + patient_weight
                        
                        # Increase the assigned nurse's hours worked this week.
                        # We keep track of this so we don't push them beyond the number of hours they're meant to work in a week.
                        new_hours = self.weekly_list.at[assigned_nurse, "hours_this_week"] + assigned_nurse_shift_length
                        
                        self.weekly_list.at[assigned_nurse, "hours_this_week"] = new_hours
                        self.staff.at[assigned_nurse, "hours_this_week"] = new_hours
                        
                        # Increase patient count for the nurse being assigned.
                        new_patient_count = self.weekly_list.at[assigned_nurse, "patients"] + 1
                        
                        self.weekly_list.at[assigned_nurse, "patients"] = new_patient_count
                        self.staff.at[assigned_nurse, "patients"] = new_patient_count
                        
                        logging.info(f"{assigned_nurse} assigned to {patient_name} for a {assigned_nurse_shift_length} hour shift. {assigned_nurse} has now worked {self.weekly_list.at[assigned_nurse, 'hours_this_week']} hours.")
                        
                        # Save a variable for the max hours this nurse has worked this week.
                        nurse_maximum_weekly_hours = self.weekly_list.at[assigned_nurse, "weekly_hours"]
                        
                        # And for how many they've actually worked so far.
                        nurse_hours_worked = self.weekly_list.at[assigned_nurse, "hours_this_week"]
                        
                        # If the assigned nurse has now hit their max hours for the week, they are removed from both the daily list and the weekly list.
                        if nurse_hours_worked >= nurse_maximum_weekly_hours:
                            
                            self.weekly_list = self.weekly_list.drop(assigned_nurse)
                            self.daily_list = self.daily_list.drop(assigned_nurse)
                            
                        # Remove the nurse from the eligible list so they are not assigned to the same patient for a double shift.
                        # self._remove_from_list(assigned_nurse, "daily")
                        logging.info(f"{assigned_nurse} removed from being assigned again to {patient_name}.")
        
        # self.schedule.insert(0,"day", self.schedule.index.day_name())
        print(self.schedule, self.staff)
        
        # Save schedule to csv.
        try: self.schedule.to_csv("data/schedule.csv")
        except PermissionError: logging.error(f"The schedule csv is open somewhere. Please close it and run the program again.")
        
        return self

Schedule().daily_schedule()