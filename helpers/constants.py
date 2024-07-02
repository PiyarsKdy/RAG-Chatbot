
check_availability = {
    "name": "check_availability",
    "description": "allows users to check slot availability on calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "date in YYYY-MM-DD format to check availability, By default, None is taken",
            },
            "time": {
                "type": "string",
                "description": "time in HH:MM:SS format to check availability, By default, None is taken",
            }
        },
    },
}

book_event = {
    "name": "book_event",
    "description": "allows users to book slot or event on calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "date in YYYY-MM-DD format to book event. By default, keep it null",
            },
            "time": {
                "type": "string",
                "description": "time in HH:MM:SS format to book event. By default, keep it null",
            },
            "book": {
                "type": "boolean",
                "description": "Always asks for user confirmation. If user confirms to book an event then only make it true, False by default.",
            }
        },
        "required": ["book"]
    },
}