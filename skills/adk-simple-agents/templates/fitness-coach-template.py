"""
Fitness Coach Agent Template

A simple, ready-to-use agent that provides personalized fitness advice,
workout recommendations, and health guidance.

Usage:
    from fitness_coach_template import create_fitness_coach

    coach = create_fitness_coach(personality="motivational")
    response = coach.ask("Create a beginner workout plan")
    print(response)
"""

from adk_bidi.agents import SimpleAgent
from adk_bidi.core import Tool
from typing import Optional


# Define fitness tools
fitness_tools = [
    Tool(
        name="calculate_bmi",
        description="Calculate BMI given height and weight",
        parameters={
            "height_cm": "Height in centimeters",
            "weight_kg": "Weight in kilograms"
        }
    ),
    Tool(
        name="calculate_calories",
        description="Calculate daily calorie requirements",
        parameters={
            "age": "Age in years",
            "gender": "Male or Female",
            "activity_level": "Sedentary, Light, Moderate, Active, Very Active",
            "weight_kg": "Weight in kilograms"
        }
    ),
    Tool(
        name="get_workout_plan",
        description="Retrieve a workout plan for a specific fitness level and goal",
        parameters={
            "fitness_level": "Beginner, Intermediate, Advanced",
            "goal": "Weight Loss, Muscle Gain, Endurance, Strength, Flexibility",
            "duration_minutes": "Workout duration in minutes"
        }
    ),
    Tool(
        name="get_nutrition_tips",
        description="Get nutrition tips for specific goals",
        parameters={
            "goal": "Weight Loss, Muscle Gain, Energy, Recovery",
            "dietary_restriction": "None, Vegetarian, Vegan, Gluten-Free, Keto"
        }
    )
]


# System prompt for fitness coach
FITNESS_COACH_SYSTEM_PROMPT = """You are an enthusiastic and knowledgeable Fitness Coach AI assistant.

Your role is to:
- Provide personalized fitness advice based on the user's goals, fitness level, and preferences
- Create customized workout plans that are safe and effective
- Offer nutritional guidance that supports fitness goals
- Motivate and encourage users to achieve their fitness objectives
- Answer questions about exercise, nutrition, and overall health
- Adapt recommendations based on user feedback and progress

Personality traits:
- Motivational and encouraging
- Knowledgeable about fitness science
- Empathetic to user challenges
- Focused on sustainable, healthy approaches
- Professional but approachable

When providing fitness advice:
1. Always consider the user's current fitness level and experience
2. Emphasize safety and proper form
3. Provide progressions from easier to harder exercises
4. Suggest modifications for different abilities
5. Encourage consistency over perfection
6. Ask clarifying questions about goals, constraints, and preferences

Remember: You're here to inspire and guide, not judge or pressure."""


def create_fitness_coach(
    personality: str = "motivational",
    specialization: Optional[str] = None,
    enable_tools: bool = True
) -> SimpleAgent:
    """
    Create a Fitness Coach agent with customizable personality and specialization.

    Args:
        personality: "motivational", "educational", or "strict"
        specialization: Optional specialization (e.g., "yoga", "bodybuilding", "running")
        enable_tools: Whether to enable fitness calculation tools

    Returns:
        Configured SimpleAgent instance
    """

    # Adjust system prompt based on personality
    prompt = FITNESS_COACH_SYSTEM_PROMPT

    if personality == "strict":
        prompt = prompt.replace(
            "Personality traits:",
            "Personality traits:\n- Direct and no-nonsense\n- Demanding high standards\n- Results-focused\n- Challenge-oriented\n\nPersonity traits (original):"
        )
    elif personality == "educational":
        prompt = prompt.replace(
            "Personality traits:",
            "Personality traits:\n- Educational and informative\n- Science-based explanations\n- Detailed breakdowns\n- Focus on understanding\n\nPersonality traits (original):"
        )

    # Add specialization if provided
    if specialization:
        specialization_prompts = {
            "yoga": "Emphasize flexibility, balance, and mind-body connection. Incorporate yoga philosophy and breathing techniques.",
            "bodybuilding": "Focus on hypertrophy, progressive overload, and muscle-building nutrition. Provide advanced training splits.",
            "running": "Specialize in running training, injury prevention, pacing strategies, and endurance building.",
            "crossfit": "Focus on functional fitness, high-intensity training, and Olympic lifting fundamentals.",
            "pilates": "Emphasize core strength, controlled movements, and postural alignment.",
            "strength": "Focus on compound lifts, progressive resistance, and strength development protocols."
        }

        if specialization in specialization_prompts:
            prompt += f"\n\nSpecialization: {specialization_prompts[specialization]}"

    # Create agent
    agent = SimpleAgent(
        name="Fitness Coach",
        system_prompt=prompt,
        model="gemini-2.5-flash",
        temperature=0.7
    )

    # Add tools if enabled
    if enable_tools:
        for tool in fitness_tools:
            agent.add_tool(tool)

    return agent


# Example fitness workout data
BEGINNER_WORKOUTS = {
    "weight_loss": {
        "Monday": "30 min cardio (walking, cycling, or swimming) + 10 min stretching",
        "Wednesday": "Bodyweight circuit: 3 sets of (10 push-ups, 15 squats, 10 lunges per leg)",
        "Friday": "30 min cardio + 10 min core work"
    },
    "muscle_gain": {
        "Monday": "Chest & Triceps: Bench press 3x8, Incline press 3x8, Tricep dips 3x10",
        "Wednesday": "Back & Biceps: Rows 3x8, Pull-ups 3x5, Curls 3x10",
        "Friday": "Legs: Squats 3x8, Deadlifts 3x5, Leg press 3x10"
    },
    "flexibility": {
        "Daily": "10 min yoga flow (sun salutations, stretches)",
        "Monday": "Beginner yoga class (30-45 min)",
        "Wednesday": "Yin yoga (60 min)",
        "Friday": "Vinyasa flow (45 min)"
    }
}


if __name__ == "__main__":
    # Example usage

    # Create a motivational fitness coach
    coach = create_fitness_coach(personality="motivational")

    # Example questions
    questions = [
        "I'm a complete beginner. Where do I start?",
        "Create a beginner workout for Monday",
        "What should I eat to build muscle?",
        "How often should I work out?"
    ]

    print("Fitness Coach Agent Demo")
    print("=" * 50)

    for question in questions:
        print(f"\nUser: {question}")
        response = coach.ask(question)
        print(f"Coach: {response}\n")
        print("-" * 50)

    # Example with specialization
    print("\n\nYoga Specialist Coach Demo")
    print("=" * 50)

    yoga_coach = create_fitness_coach(
        personality="educational",
        specialization="yoga"
    )

    yoga_question = "What are the benefits of practicing yoga regularly?"
    print(f"\nUser: {yoga_question}")
    response = yoga_coach.ask(yoga_question)
    print(f"Coach: {response}\n")
