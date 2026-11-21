# TechPanda Academy Admissions WhatsApp Automation Flow Template

def get_default_admissions_flow_data():
    return {
        "nodes": [
            {
                "x": 100,
                "y": 80,
                "id": "trigger_1",
                "data": {
                    "title": "Trigger",
                    "keywords": "hi, hello, course, restart, start",
                    "trigger_type": "first_incoming_message"
                },
                "type": "trigger",
                "title": "Trigger",
                "position": {
                    "x": 100,
                    "y": 80
                },
                "next_node_id": "msg_1",
                "trigger_type": "first_incoming_message",
                "trigger_keywords": "hi, hello, course, restart, start"
            },
            {
                "x": 380,
                "y": 80,
                "id": "msg_1",
                "body": "👋 Welcome to TechPanda – Software Training & Placement Institute!\n\nThank you for reaching out! 😊 We're happy to assist you. Please share your name and let us know your queries about courses, batches, training, or placements. Our team will be happy to help you!",
                "data": {
                    "text": "👋 Welcome to TechPanda – Software Training & Placement Institute!\n\nThank you for reaching out! 😊 We're happy to assist you. Please share your name and let us know your queries about courses, batches, training, or placements. Our team will be happy to help you!",
                    "title": "Welcome Message"
                },
                "type": "message",
                "title": "Welcome Message",
                "position": {
                    "x": 380,
                    "y": 80
                },
                "next_node_id": "node_buttons_7461"
            },
            {
                "x": 380,
                "y": 360,
                "id": "node_buttons_7461",
                "body": "What are you looking for?",
                "data": {
                    "text": "What are you looking for?",
                    "title": "Q1: What are you looking for?",
                    "footer": "Select an option",
                    "header": "Question 1",
                    "options": [
                        {
                            "id": "opt_1",
                            "title": "Training",
                            "next_node_id": "node_buttons_8415"
                        },
                        {
                            "id": "opt_2",
                            "title": "Train + Placement",
                            "next_node_id": "node_buttons_8415"
                        }
                    ],
                    "variable_name": "interest_type"
                },
                "type": "buttons",
                "title": "Q1: What are you looking for?",
                "footer": "Select an option",
                "header": "Question 1",
                "options": [
                    {
                        "id": "opt_1",
                        "title": "Training",
                        "next_node_id": "node_buttons_8415"
                    },
                    {
                        "id": "opt_2",
                        "title": "Train + Placement",
                        "next_node_id": "node_buttons_8415"
                    }
                ],
                "position": {
                    "x": 380,
                    "y": 360
                },
                "next_node_id": None,
                "variable_name": "interest_type"
            },
            {
                "x": 720,
                "y": 360,
                "id": "node_buttons_8415",
                "body": "When are you planning to join?",
                "data": {
                    "text": "When are you planning to join?",
                    "title": "Q2: When are you planning to join?",
                    "footer": "Select timeframe",
                    "header": "Question 2",
                    "options": [
                        {
                            "id": "opt_1",
                            "title": "Immediately",
                            "next_node_id": "node_list_q3"
                        },
                        {
                            "id": "opt_2",
                            "title": "Within 7 Days",
                            "next_node_id": "node_list_q3"
                        },
                        {
                            "id": "opt_3",
                            "title": "Within 15 Days",
                            "next_node_id": "node_list_q3"
                        }
                    ],
                    "variable_name": "joining_timeframe"
                },
                "type": "buttons",
                "title": "Q2: When are you planning to join?",
                "footer": "Select timeframe",
                "header": "Question 2",
                "options": [
                    {
                        "id": "opt_1",
                        "title": "Immediately",
                        "next_node_id": "node_list_q3"
                    },
                    {
                        "id": "opt_2",
                        "title": "Within 7 Days",
                        "next_node_id": "node_list_q3"
                    },
                    {
                        "id": "opt_3",
                        "title": "Within 15 Days",
                        "next_node_id": "node_list_q3"
                    }
                ],
                "position": {
                    "x": 720,
                    "y": 360
                },
                "next_node_id": None,
                "variable_name": "joining_timeframe"
            },
            {
                "x": 1060,
                "y": 360,
                "id": "node_list_q3",
                "body": "What is your current status?",
                "data": {
                    "text": "What is your current status?",
                    "title": "Q3: What is your current status?",
                    "footer": "Tap button to view choices",
                    "header": "Current Status",
                    "source": "custom",
                    "sections": [
                        {
                            "rows": [
                                {
                                    "id": "row_1",
                                    "title": "College Student",
                                    "description": "Currently enrolled"
                                },
                                {
                                    "id": "row_2",
                                    "title": "Fresher / Job Seeker",
                                    "description": "Looking for employment"
                                },
                                {
                                    "id": "row_3",
                                    "title": "Working Professional",
                                    "description": "Up-skilling"
                                }
                            ],
                            "title": "Status Options"
                        }
                    ],
                    "button_text": "Select Status",
                    "variable_name": "student_status"
                },
                "type": "list",
                "title": "Q3: What is your current status?",
                "footer": "Tap button to view choices",
                "header": "Current Status",
                "source": "custom",
                "position": {
                    "x": 1060,
                    "y": 360
                },
                "sections": [
                    {
                        "rows": [
                            {
                                "id": "row_1",
                                "title": "College Student",
                                "description": "Currently enrolled"
                            },
                            {
                                "id": "row_2",
                                "title": "Fresher / Job Seeker",
                                "description": "Looking for employment"
                            },
                            {
                                "id": "row_3",
                                "title": "Working Professional",
                                "description": "Up-skilling"
                            }
                        ],
                        "title": "Status Options"
                    }
                ],
                "button_text": "Select Status",
                "next_node_id": "node_buttons_q4",
                "variable_name": "student_status"
            },
            {
                "x": 1060,
                "y": 680,
                "id": "node_buttons_q4",
                "body": "Preferred training mode?",
                "data": {
                    "text": "Preferred training mode?",
                    "title": "Q4: Preferred training mode?",
                    "footer": "Select your mode",
                    "header": "Training Mode",
                    "options": [
                        {
                            "id": "opt_1",
                            "title": "Classroom (Chennai)",
                            "next_node_id": "end_1"
                        },
                        {
                            "id": "opt_2",
                            "title": "Online Training",
                            "next_node_id": "end_1"
                        }
                    ],
                    "variable_name": "training_mode"
                },
                "type": "buttons",
                "title": "Q4: Preferred training mode?",
                "footer": "Select your mode",
                "header": "Training Mode",
                "options": [
                    {
                        "id": "opt_1",
                        "title": "Classroom (Chennai)",
                        "next_node_id": "end_1"
                    },
                    {
                        "id": "opt_2",
                        "title": "Online Training",
                        "next_node_id": "end_1"
                    }
                ],
                "position": {
                    "x": 1060,
                    "y": 680
                },
                "next_node_id": None,
                "variable_name": "training_mode"
            },
            {
                "x": 380,
                "y": 680,
                "id": "end_1",
                "body": "Thank you for your interest in **TechPanda Academy!** 💙\n\nOur team will help you with course details, available batches and career guidance.\n\n🌐 Website: https://itechpanda.com/\n\nLet's build your future! 🚀",
                "data": {
                    "text": "Thank you for your interest in **TechPanda Academy!** 💙\n\nOur team will help you with course details, available batches and career guidance.\n\n🌐 Website: https://itechpanda.com/\n\nLet's build your future! 🚀",
                    "title": "End Session"
                },
                "type": "end",
                "title": "End Session",
                "position": {
                    "x": 380,
                    "y": 680
                },
                "next_node_id": None
            }
        ],
        "viewport": {
            "x": 0,
            "y": 0,
            "zoom": 1
        },
        "connections": [
            {
                "id": "c_trig_msg",
                "source": "trigger_1",
                "target": "msg_1",
                "target_input": "input",
                "source_output": "default"
            },
            {
                "id": "c_msg_q1",
                "source": "msg_1",
                "target": "node_buttons_7461",
                "target_input": "input",
                "source_output": "default"
            },
            {
                "id": "c_q1_opt1_q2",
                "source": "node_buttons_7461",
                "target": "node_buttons_8415",
                "target_input": "input",
                "source_output": "opt_1"
            },
            {
                "id": "c_q1_opt2_q2",
                "source": "node_buttons_7461",
                "target": "node_buttons_8415",
                "target_input": "input",
                "source_output": "opt_2"
            },
            {
                "id": "c_q2_opt1_q3",
                "source": "node_buttons_8415",
                "target": "node_list_q3",
                "target_input": "input",
                "source_output": "opt_1"
            },
            {
                "id": "c_q2_opt2_q3",
                "source": "node_buttons_8415",
                "target": "node_list_q3",
                "target_input": "input",
                "source_output": "opt_2"
            },
            {
                "id": "c_q2_opt3_q3",
                "source": "node_buttons_8415",
                "target": "node_list_q3",
                "target_input": "input",
                "source_output": "opt_3"
            },
            {
                "id": "c_q3_q4",
                "source": "node_list_q3",
                "target": "node_buttons_q4",
                "target_input": "input",
                "source_output": "default"
            },
            {
                "id": "c_q4_opt1_end",
                "source": "node_buttons_q4",
                "target": "end_1",
                "target_input": "input",
                "source_output": "opt_1"
            },
            {
                "id": "c_q4_opt2_end",
                "source": "node_buttons_q4",
                "target": "end_1",
                "target_input": "input",
                "source_output": "opt_2"
            }
        ]
    }
