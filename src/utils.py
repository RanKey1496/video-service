from termcolor import colored

def print_colored(text, color="green"):
    print(colored(f"=> {text}", color))
    
def print_info(text):
    print_colored(text, "blue")
    
def print_error(text):
    print_colored(text, "red")
    
def print_warning(text):
    print_colored(text, "yellow")
    
def print_success(text):
    print_colored(text, "green")