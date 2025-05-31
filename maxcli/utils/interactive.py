"""Interactive prompt utilities."""
import sys
from typing import Optional, List, Tuple

def prompt_for_config_value(prompt: str, current_value: Optional[str] = None, required: bool = True) -> str:
    """Prompt user for a configuration value with optional current value display."""
    try:
        import questionary
        
        if current_value:
            value = questionary.text(
                f"{prompt} (current: {current_value})",
                default=current_value,
                style=questionary.Style([
                    ('question', 'bold'),
                    ('answer', 'bold fg:#2ecc71')
                ])
            ).ask()
        else:
            value = questionary.text(
                prompt,
                style=questionary.Style([
                    ('question', 'bold'),
                    ('answer', 'bold fg:#2ecc71')
                ])
            ).ask()
        
        if value is None:
            if required:
                print("❌ This field is required. Please provide a value.")
                return prompt_for_config_value(prompt, current_value, required)
            else:
                return ""
        
        value = value.strip()
        
        if required and not value:
            print("❌ This field is required. Please provide a value.")
            return prompt_for_config_value(prompt, current_value, required)
        
        return value
        
    except ImportError:
        return _prompt_for_config_value_fallback(prompt, current_value, required)

def _prompt_for_config_value_fallback(prompt: str, current_value: Optional[str] = None, required: bool = True) -> str:
    """Fallback input function with readline support."""
    sys.stdout.flush()
    sys.stderr.flush()
    
    if current_value:
        full_prompt = f"{prompt} (current: {current_value}): "
        print(f"💡 Press Enter to keep current value, or type new value")
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        try:
            value = input(full_prompt).strip()
            
            if not value and current_value:
                return current_value
            
            if value:
                return value
            
            if required:
                print("❌ This field is required. Please provide a value.")
            else:
                return ""
                
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Input cancelled.")
            sys.exit(1)

def interactive_selection(title: str, choices: List[str]) -> Optional[str]:
    """Show interactive menu for selection."""
    if not choices:
        return None
    
    try:
        import questionary
        
        selected = questionary.select(
            title,
            choices=choices,
            style=questionary.Style([
                ('question', 'bold'),
                ('highlighted', 'bold bg:#3498db fg:#ffffff'),
                ('pointer', 'bold'),
                ('answer', 'bold fg:#2ecc71')
            ])
        ).ask()
        
        return selected
        
    except ImportError:
        return _interactive_selection_fallback(title, choices)

def _interactive_selection_fallback(title: str, choices: List[str]) -> Optional[str]:
    """Fallback selection with numbered menu."""
    print(f"\n{title}")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    
    while True:
        try:
            choice = input(f"\nSelect option (1-{len(choices)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                return None
                
            index = int(choice) - 1
            if 0 <= index < len(choices):
                return choices[index]
            else:
                print(f"❌ Please enter a number between 1 and {len(choices)}")
                
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Selection cancelled.")
            return None

def interactive_checkbox(title: str, choices: List[Tuple[str, str]]) -> List[str]:
    """Show interactive checkbox menu for multiple selection."""
    try:
        import questionary
        
        app_choices = [f"{name} - {desc}" for name, desc in choices]
        
        # Add special options
        all_choice = "✅ Select ALL items (recommended)"
        none_choice = "❌ Select NO items (skip this step)"
        custom_choice = "🔧 Let me choose specific items"
        
        mode = questionary.select(
            title,
            choices=[all_choice, custom_choice, none_choice],
            style=questionary.Style([
                ('question', 'bold'),
                ('highlighted', 'bold bg:#3498db fg:#ffffff'),
                ('pointer', 'bold'),
                ('answer', 'bold fg:#2ecc71')
            ])
        ).ask()
        
        if mode is None or mode == none_choice:
            return []
        elif mode == all_choice:
            return [name for name, _ in choices]
        else:  # custom_choice
            selected = questionary.checkbox(
                "Select items (use Space to select, Enter to confirm):",
                choices=app_choices,
                style=questionary.Style([
                    ('question', 'bold'),
                    ('highlighted', 'bold bg:#3498db fg:#ffffff'),
                    ('pointer', 'bold'),
                    ('answer', 'bold fg:#2ecc71'),
                    ('selected', 'fg:#2ecc71')
                ])
            ).ask()
            
            if selected is None:
                return []
                
            return [choice.split(" - ")[0] for choice in selected]
        
    except ImportError:
        return _interactive_checkbox_fallback(title, choices)

def _interactive_checkbox_fallback(title: str, choices: List[Tuple[str, str]]) -> List[str]:
    """Fallback checkbox selection."""
    print(f"\n{title}")
    print("0. Select ALL items (recommended)")
    print("99. Select NO items (skip)")
    print("=" * 50)
    
    for i, (name, desc) in enumerate(choices, 1):
        print(f"{i:2d}. {name} - {desc}")
    
    while True:
        try:
            choice = input(f"\nSelect option (0=all, 99=none, comma-separated for multiple): ").strip()
            
            if choice == "0":
                return [name for name, _ in choices]
            elif choice == "99":
                return []
            else:
                indices = [int(part.strip()) for part in choice.split(",") if part.strip()]
                selected = []
                for index in indices:
                    if 1 <= index <= len(choices):
                        selected.append(choices[index - 1][0])
                    else:
                        print(f"❌ Invalid choice: {index}")
                        break
                else:
                    return selected
                        
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Selection cancelled.")
            return [] 