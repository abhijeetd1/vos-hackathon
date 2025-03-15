import functions_framework
from pydantic import BaseModel
from typing import List, Optional
import logging
import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime
import os
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger("VOS-FULFILMENT")

# Initialize Firebase Admin SDK
try:
    # Check if already initialized
    app = firebase_admin.get_app()
    logger.info("Firebase app already initialized")
except ValueError:
    # Initialize with credentials
    try:
        cred = credentials.Certificate('firebase-key.json')
        firebase_admin.initialize_app(cred, {
            'projectId': 'burner-abhdey0',
        })
        logger.info("Firebase app initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}")
        raise

# Get Firestore client for mcd-vos database
db = firestore.Client(
    project='burner-abhdey0',
    database='mcd-vos'
)
logger.info("Initialized Firestore client with mcd-vos database")

class FoodItem(BaseModel):
    item_id: str
    name: str
    quantity: int = 1
    base_price: float
    customizations: List[str] = []
    item_total: float

class DrinkItem(BaseModel):
    item_id: str
    name: str
    quantity: int = 1
    base_price: float
    size: Optional[str] = None
    size_price: float = 0
    item_total: float

# In-memory session storage (for tracking current order during conversation)
active_sessions = {}

def get_menu_item(item_name: str):
    """Fetch menu item with case-insensitive search and ensure correct data types."""
    try:
        logger.info(f"Attempting to fetch menu item: {item_name}")
        menu_ref = db.collection('menu_items')
        
        # Get all menu items and filter case-insensitively updated
        menu_items = menu_ref.get()
        for doc in menu_items:
            item_data = doc.to_dict()
            if item_data['name'].lower() == item_name.lower():
                # Add document ID to the item data
                item_data['id'] = doc.id
                
                # Ensure base_price is a float
                try:
                    item_data['base_price'] = float(item_data['base_price'])
                except (ValueError, TypeError):
                    logger.error(f"Invalid base_price format for {item_name}")
                    continue
                
                # Ensure sizes are floats if they exist
                if item_data.get('has_size') and 'sizes' in item_data:
                    item_data['sizes'] = {
                        size: float(price)
                        for size, price in item_data['sizes'].items()
                    }
                
                logger.info(f"Found menu item with validated data types: {item_data}")
                return item_data
        
        logger.info(f"Menu item not found: {item_name}")
        return None

    except Exception as e:
        logger.error(f"Error fetching menu item: {e}")
        return None

def calculate_item_total(menu_item, quantity: int, size: Optional[str] = None):
    """Calculate total price for an item including size if applicable."""
    try:
        # Convert base_price from string to float if necessary
        base_price = float(menu_item['base_price'])
        size_price = 0.0
        
        if menu_item.get('has_size', False) and size and 'sizes' in menu_item:
            size_price = float(menu_item['sizes'].get(size.lower(), 0))
        
        total = (base_price + size_price) * quantity
        return total, size_price
    except (ValueError, TypeError) as e:
        logger.error(f"Error calculating item total: {str(e)}")
        logger.error(f"Menu item data: {menu_item}")
        raise

def get_order_summary(session_id: str):
    """
    Creates a formatted order summary including all items and total amount.
    Now includes proper customization details in the response.
    """
    try:
        # Always return a summary structure, even if empty
        summary = {
            "items": [],
            "total_amount": 0,
            "item_count": 0
        }
        
        if session_id in active_sessions and active_sessions[session_id]["items"]:
            session = active_sessions[session_id]
            
            # Format items with customizations
            formatted_items = []
            for item in session["items"]:
                formatted_item = {
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "base_price": item["base_price"],
                    "customizations": item.get("customizations", []),  # Ensure customizations are included
                    "item_total": item["item_total"]
                }
                
                # Add size info for drinks if present
                if "size" in item:
                    formatted_item["size"] = item["size"]
                if "size_price" in item:
                    formatted_item["size_price"] = item["size_price"]
                
                formatted_items.append(formatted_item)
            
            summary.update({
                "items": formatted_items,
                "total_amount": session["total_amount"],
                "item_count": sum(item["quantity"] for item in session["items"])
            })
            
        return {"order_summary": summary}
    except Exception as e:
        logger.error(f"Error creating order summary: {str(e)}")
        return {"order_summary": {"items": [], "total_amount": 0, "item_count": 0}}

def create_response(fulfillment_text: str, session_id: str, output_contexts=None):
    """Creates a standardized response with detailed order summary."""
    # Get order summary
    order_summary = get_order_summary(session_id)
    
    # If this is a response about completed order, format items with customizations
    if "completed" in fulfillment_text.lower() or "order is:" in fulfillment_text.lower():
        if session_id in active_sessions and active_sessions[session_id]["items"]:
            items_descriptions = [
                format_item_description(item) 
                for item in active_sessions[session_id]["items"]
            ]
            
            total_amount = active_sessions[session_id]["total_amount"]
            
            fulfillment_text = (
                f"Great! Your order is: {', '.join(items_descriptions)}. "
                f"Total amount: ${total_amount:.2f}. "
                "Please proceed to next window for payment."
            )
    
    response = {
        "fulfillmentText": fulfillment_text,
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [fulfillment_text]
                }
            }
        ],
        "payload": order_summary
    }

    # Add output contexts if provided
    if output_contexts:
        response["outputContexts"] = output_contexts
    
    logger.info(f"Response created with order summary and contexts: {output_contexts}")
    return response

@functions_framework.http
def handle_request(request):
    """Main entry point for the Cloud Function."""
    try:
        logger.info("Received request")
        request_json = request.get_json()
        logger.info(f"Request body: {request_json}")

        response = dialogflow_webhook(request_json)
        logger.info(f"Response: {response}")
        return response
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            "error": str(e), 
            "fulfillmentText": "Sorry, there was an error processing your request."
        }

def dialogflow_webhook(data: dict):
    """Handles webhook requests from Dialogflow."""
    try:
        intent_name = data["queryResult"]["intent"]["displayName"]
        
        # Extract session ID from outputContexts
        output_contexts = data["queryResult"].get("outputContexts", [])
        if not output_contexts:
            raise ValueError("No output contexts found in request")
            
        # Extract session ID from the first context's name
        context_name = output_contexts[0]["name"]
        session_id = context_name.split("/sessions/")[1].split("/contexts/")[0]

        logger.info(f"Intent: {intent_name}")
        logger.info(f"Session ID: {session_id}")

        # Initialize session if it doesn't exist
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                "items": [],
                "total_amount": 0
            }

        # Map intents to their handlers
        intent_handlers = {
            "order.food": handle_order_food,
            "order.modify": handle_order_modify,
            "order.drink": handle_order_drink,
            "order.size": handle_size_update,
            "order.remove": handle_order_remove,
            "order.complete": handle_order_complete,
            "order.combined": handle_order_combined,
            "order.quantity": handle_order_quantity,  # Add the new handler
            "order.limit.acknowledge": handle_order_limit_acknowledge,
            "order.complete.acknowledge": handle_order_complete_acknowledge
        }

        # Get the appropriate handler for the intent
        handler = intent_handlers.get(intent_name)
        
        if handler:
            return handler(data, session_id)
        else:
            logger.warning(f"No handler found for intent: {intent_name}")
            return create_response(
                "I'm not sure how to handle that request. Could you please try again?",
                session_id
            )
    
    except Exception as e:
        logger.error(f"Error in dialogflow_webhook: {str(e)}", exc_info=True)
        return {
            "fulfillmentText": "Sorry, there was an error processing your request.",
            "payload": {
                "order_summary": {
                    "items": [],
                    "total_amount": 0,
                    "item_count": 0
                }
            }
        }

def handle_order_food(data: dict, session_id: str):
    """Handles the 'order.food' intent with multiple customization support and size handling."""
    try:
        # Extract basic order details
        parameters = data["queryResult"]["parameters"]
        food_item_param = parameters.get("food-item")
        modification_types = parameters.get("modification-type", [])
        food_components = parameters.get("food-components", [])
        size = parameters.get("drink-size")  # Reuse drink-size parameter for food sizes
        
        # Handle food item whether it's a string or array
        food_item = food_item_param[0] if isinstance(food_item_param, list) else food_item_param
        
        if not food_item:
            return create_response(
                "I'm sorry, I didn't catch what food item you wanted. Could you please repeat that?",
                session_id
            )

        # Get menu item details
        menu_item = get_menu_item(food_item)
        if not menu_item:
            return create_response(
                f"I'm sorry, we don't have {food_item} on our menu.",
                session_id
            )

        # Handle quantity parameter
        quantity_param = parameters.get("number", 1)
        try:
            quantity = int(float(quantity_param))
        except (ValueError, TypeError):
            quantity = 1
        logger.info(f"Quantity parsed: {quantity}")

        # Extract project_id from session name
        project_id = data["session"].split('/')[1]

        # Initialize customizations list
        customizations = []

        # Ensure modification_types and food_components are lists
        if not isinstance(modification_types, list):
            modification_types = [modification_types]
        if not isinstance(food_components, list):
            food_components = [food_components]

        # Process multiple customizations if provided
        if modification_types and food_components:
            logger.info(f"Processing customizations: {modification_types} {food_components}")
            
            # Process each customization pair
            for mod_type, component in zip(modification_types, food_components):
                if mod_type and component:
                    # Validate each customization
                    is_valid, message = validate_customization(menu_item, mod_type, component)
                    if not is_valid:
                        return create_response(message, session_id)

                    # Format customization based on type
                    if mod_type in ["no", "without"]:
                        customizations.append(f"no {component}")
                    elif mod_type in ["extra", "add"]:
                        customizations.append(f"extra {component}")
                    elif mod_type in ["light", "heavy"]:
                        customizations.append(f"{mod_type} {component}")

        # Validate quantity before processing
        is_valid, validation_message, contexts = validate_order_quantity(
            menu_item["id"], 
            "food",
            quantity,
            session_id,
            project_id
        )
        
        if not is_valid:
            return create_response(validation_message, session_id, contexts)

        # Check if this item supports sizes and if a size is needed
        if menu_item.get("has_size", False):
            if not size:
                # Create context to remember we're waiting for size
                size_context = [{
                    "name": f"projects/{project_id}/agent/sessions/{session_id}/contexts/awaiting-size",
                    "lifespanCount": 2,
                    "parameters": {
                        "item_name": food_item,
                        "item_type": "food"
                    }
                }]
                
                return create_response(
                    f"What size would you like for your {food_item}?",
                    session_id,
                    size_context
                )
            item_total, size_price = calculate_item_total(menu_item, quantity, size)
        else:
            item_total = menu_item["base_price"] * quantity
            size_price = 0
            size = None  # Ensure size is None for items that don't support sizes

        # Create order item
        order_item = {
            "item_id": menu_item["id"],
            "name": menu_item["name"],
            "quantity": quantity,
            "base_price": menu_item["base_price"],
            "customizations": customizations,
        }

        # Add size information if the item supports sizes
        if menu_item.get("has_size", False):
            order_item.update({
                "size": size,
                "size_price": size_price,
            })

        order_item["item_total"] = item_total

        # Initialize session if it doesn't exist
        if session_id not in active_sessions:
            active_sessions[session_id] = {"items": [], "total_amount": 0}
        
        # Add item to session
        active_sessions[session_id]["items"].append(order_item)
        active_sessions[session_id]["total_amount"] += item_total

        # Create response text based on whether customizations were requested
        response_text = f"Okay, I've added {quantity} "
        if size:
            response_text += f"{size} "
        response_text += menu_item['name']
        if customizations:
            response_text += f" with {', '.join(customizations)}"
        response_text += ". Would you like anything else?"

        return create_response(response_text, session_id)

    except Exception as e:
        logger.error(f"Error in handle_order_food: {str(e)}", exc_info=True)
        raise
    
def handle_order_drink(data: dict, session_id: str):
    """Handles the 'order.drink' intent."""
    try:
        # Extract parameters
        parameters = data["queryResult"]["parameters"]
        drink_item = parameters.get("drink-item")
        size = parameters.get("drink-size")
        quantity_param = parameters.get("number", 1)
        
        try:
            quantity = int(float(quantity_param))
        except (ValueError, TypeError):
            quantity = 1
        logger.info(f"Quantity parsed: {quantity}")

        # Skip processing if we only got a size parameter (likely meant for size intent)
        if not drink_item and size:
            return create_response(
                "I didn't catch which drink you wanted. Could you please specify your drink?",
                session_id
            )

        # Fetch menu item details
        menu_item = get_menu_item(drink_item)
        if not menu_item:
            return create_response(
                f"I'm sorry, we don't have {drink_item} on our menu.",
                session_id
            )

        # Extract project_id from session name for context creation
        project_id = data["session"].split('/')[1]

        # Validate quantity before processing
        is_valid, validation_message, contexts = validate_order_quantity(
            menu_item["id"], 
            "drink",
            quantity,
            session_id,
            project_id
        )
        
        if not is_valid:
            return create_response(validation_message, session_id, contexts)

        # Calculate total
        item_total, size_price = calculate_item_total(menu_item, quantity, size)

        # Create order item
        order_item = {
            "item_id": menu_item["id"],
            "name": menu_item["name"],
            "quantity": quantity,
            "base_price": menu_item["base_price"],
            "size": size,
            "size_price": size_price,
            "item_total": item_total
        }

        # Initialize session if it doesn't exist
        if session_id not in active_sessions:
            active_sessions[session_id] = {"items": [], "total_amount": 0}

        # Add item to session
        active_sessions[session_id]["items"].append(order_item)
        active_sessions[session_id]["total_amount"] += item_total

        if not size and menu_item.get("has_size", False):
            # Create awaiting-size context
            size_context = [{
                "name": f"projects/{project_id}/agent/sessions/{session_id}/contexts/awaiting-size",
                "lifespanCount": 2,
                "parameters": {
                    "item_name": drink_item,
                    "item_type": "drink"
                }
            }]
            return create_response(
                f"What size would you like for your {drink_item}?",
                session_id,
                size_context
            )
        
        # Create response based on whether size was specified
        response_text = f"Okay, I've added {quantity} "
        if size:
            response_text += f"{size} "
        response_text += f"{drink_item} to your order. Anything else?"
        
        return create_response(response_text, session_id)
    
    except Exception as e:
        logger.error(f"Error in handle_order_drink: {str(e)}", exc_info=True)
        raise

def handle_size_update(data: dict, session_id: str):
    """Handles the 'order.size' intent for updating both food and drink sizes."""
    try:
        # Get all contexts
        contexts = data["queryResult"]["outputContexts"]
        
        # Get ongoing order context
        ongoing_order_context = next(
            (ctx for ctx in contexts if ctx["name"].endswith("/contexts/ongoing-order")),
            None
        )
        
        # Get awaiting-size context
        awaiting_size_context = next(
            (ctx for ctx in contexts if ctx["name"].endswith("/contexts/awaiting-size")),
            None
        )
        
        if not ongoing_order_context:
            return create_response(
                "I couldn't find your order. Could you start over?",
                session_id
            )
            
        # Extract parameters
        params = ongoing_order_context["parameters"]
        size = params.get("drink-size")

        if not size:
            return create_response(
                "I didn't catch what size you wanted. Could you please specify small, medium, or large?",
                session_id
            )

        # If no awaiting-size context, try to find the last item in session that needs size
        if not awaiting_size_context:
            if session_id in active_sessions and active_sessions[session_id]["items"]:
                session_items = active_sessions[session_id]["items"]
                last_item = session_items[-1]
                
                # Check if the last item needs size
                menu_item = get_menu_item(last_item["name"])
                if menu_item and menu_item.get("has_size", False):
                    item_name = last_item["name"]
                    item_type = "drink" if "customizations" not in last_item else "food"
                else:
                    return create_response(
                        "I'm not sure which item you want to set the size for. Could you please start over?",
                        session_id
                    )
            else:
                return create_response(
                    "I'm not sure which item you want to set the size for. Could you please start over?",
                    session_id
                )
        else:
            # Get item details from awaiting-size context
            size_params = awaiting_size_context["parameters"]
            item_name = size_params.get("item_name")
            item_type = size_params.get("item_type")

        if not item_name:
            return create_response(
                "I'm sorry, I lost track of your order. Could you please let me know what you'd like to order?",
                session_id
            )

        logger.info(f"Processing size update for {item_type} item: {item_name} with size: {size}")

        # Get menu item details
        menu_item = get_menu_item(item_name)
        if not menu_item:
            return create_response(
                f"I'm sorry, we don't have {item_name} on our menu anymore.",
                session_id
            )
            
        if not menu_item.get('has_size', False):
            return create_response(
                f"I'm sorry, but {item_name} doesn't come in different sizes.",
                session_id
            )

        # Calculate total with the new size (initially for quantity 1)
        item_total, size_price = calculate_item_total(menu_item, 1, size)
        
        # Create order item
        order_item = {
            "item_id": menu_item["id"],
            "name": menu_item["name"],
            "quantity": 1,
            "base_price": menu_item["base_price"],
            "size": size,
            "size_price": size_price,
            "item_total": item_total
        }

        # Add customizations if it's a food item
        if item_type == "food":
            order_item["customizations"] = []

        # Initialize or get session
        if session_id not in active_sessions:
            active_sessions[session_id] = {"items": [], "total_amount": 0}
            
        # Look for existing order and update
        session = active_sessions[session_id]
        updated = False
        
        for i, item in enumerate(session["items"]):
            # Look for matching item (case-insensitive)
            if item["name"].lower() == order_item["name"].lower():
                # Update existing item, preserving its original quantity
                order_item["quantity"] = item["quantity"]
                # Preserve customizations for food items
                if "customizations" in item:
                    order_item["customizations"] = item["customizations"]
                # Recalculate total with correct quantity
                order_item["item_total"] = (menu_item["base_price"] + size_price) * order_item["quantity"]
                old_total = item["item_total"]
                session["items"][i] = order_item
                session["total_amount"] = session["total_amount"] - old_total + order_item["item_total"]
                updated = True
                break
                
        if not updated:
            session["items"].append(order_item)
            session["total_amount"] += item_total
        
        # Extract project_id from session name
        project_id = data["session"].split('/')[1]

        # Clear the awaiting-size context
        clear_context = [{
            "name": f"projects/{project_id}/agent/sessions/{session_id}/contexts/awaiting-size",
            "lifespanCount": 0
        }]
        
        # Create response text
        quantity_str = f"{order_item['quantity']} " if order_item['quantity'] > 1 else ""
        response_text = f"Got it! I've updated your {item_name} to {quantity_str}{size}"
        if "customizations" in order_item and order_item["customizations"]:
            response_text += f" with {', '.join(order_item['customizations'])}"
        response_text += ". Would you like anything else?"

        return create_response(response_text, session_id, clear_context)
    
    except Exception as e:
        logger.error(f"Error in handle_size_update: {str(e)}", exc_info=True)
        raise

def handle_order_remove(data: dict, session_id: str):
    """Handles the 'order.remove' intent."""
    try:
        # Check if there's an active order
        if session_id not in active_sessions or not active_sessions[session_id]["items"]:
            return create_response(
                "There's no active order to remove items from.",
                session_id
            )

        # Get parameters
        parameters = data["queryResult"]["parameters"]
        food_items = parameters.get("food-item", [])
        drink_item = parameters.get("drink-item", "")
        
        quantity_param = parameters.get("number", 1)
        try:
            quantity = int(float(quantity_param))
        except (ValueError, TypeError):
            quantity = 1
        
        logger.info(f"Removing - Food items: {food_items}, Drink item: {drink_item}, Quantity: {quantity}")

        # Get the item to remove (either food or drink)
        item_to_remove = food_items[0] if food_items else drink_item
        if not item_to_remove:
            return create_response(
                "I'm not sure which item you want to remove. Could you please specify?",
                session_id
            )

        # Find and remove the item
        session = active_sessions[session_id]
        removed = False
        
        for i, item in enumerate(session["items"]):
            if item["name"].lower() == item_to_remove.lower():
                if item["quantity"] <= quantity:
                    # Remove the entire item
                    session["total_amount"] -= item["item_total"]
                    session["items"].pop(i)
                else:
                    # Reduce the quantity
                    old_total = item["item_total"]
                    item["quantity"] -= quantity
                    item["item_total"] = (item["item_total"] / (item["quantity"] + quantity)) * item["quantity"]
                    session["total_amount"] -= (old_total - item["item_total"])
                removed = True
                break

        if not removed:
            return create_response(
                f"I couldn't find {item_to_remove} in your order.",
                session_id
            )

        return create_response(
            f"You got it. I have removed {quantity} {item_to_remove}. Anything Else?",
            session_id
        )

    except Exception as e:
        logger.error(f"Error in handle_order_remove: {str(e)}", exc_info=True)
        raise

def handle_order_complete(data: dict, session_id: str):
    """Handles the 'order.complete' intent."""
    try:
        if session_id not in active_sessions or not active_sessions[session_id]["items"]:
            return create_response(
                "Your order is empty. What would you like to order?",
                session_id
            )

        # Create order in Firestore
        order_ref = db.collection('orders').document()
        order_data = {
            "id": order_ref.id,
            "session_id": session_id,
            "status": "completed",
            "created_at": firestore.SERVER_TIMESTAMP,
            "completed_at": firestore.SERVER_TIMESTAMP,
            "items": active_sessions[session_id]["items"],
            "total_amount": active_sessions[session_id]["total_amount"]
        }

        order_ref.set(order_data)

        # Prepare order summary
        items_summary = []
        for item in active_sessions[session_id]["items"]:
            summary = f"{item['quantity']} {item.get('size', '')} {item['name']}"
            if item.get('customizations'):
                summary += f" with {', '.join(item['customizations'])}"
            items_summary.append(summary)

        # Extract project_id from session name
        project_id = data["session"].split('/')[1]

        # Create completion context and clear all other contexts
        completion_contexts = [
            {
                "name": f"projects/{project_id}/agent/sessions/{session_id}/contexts/awaiting-completion-acknowledgment",
                "lifespanCount": 1
            },
            {
                "name": f"projects/{project_id}/agent/sessions/{session_id}/contexts/awaiting-size",
                "lifespanCount": 0  # Clear awaiting-size context
            },
            {
                "name": f"projects/{project_id}/agent/sessions/{session_id}/contexts/ongoing-order",
                "lifespanCount": 0  # Clear ongoing-order context
            }
        ]

        # Get final summary before clearing session
        final_response = create_response(
            f"Great! Your order is: {', '.join(items_summary)}. Total amount: ${active_sessions[session_id]['total_amount']:.2f}. Please proceed to next window for payment.",
            session_id,
            completion_contexts
        )

        # Clear session
        del active_sessions[session_id]

        return final_response
    
    except Exception as e:
        logger.error(f"Error in handle_order_complete: {str(e)}", exc_info=True)
        raise

def handle_order_combined(data: dict, session_id: str):
    """
    Handles the 'order.combined' intent for multiple items in a single order.
    """
    try:
        parameters = data["queryResult"]["parameters"]
        food_items = parameters.get("food-item", [])
        drink_items = parameters.get("drink-item", [])
        drink_sizes = parameters.get("drink-size", [])
        quantities = parameters.get("number", [1])  # Default to 1 if not specified
        
        # Ensure quantities list has enough values
        while len(quantities) < len(food_items) + len(drink_items):
            quantities.append(quantities[-1] if quantities else 1)
            
        response_items = []
        current_quantity_index = 0

        # Extract project_id from session name
        project_id = data["session"].split('/')[1]
        
        # Process food items
        for food_item in food_items:
            quantity = int(float(quantities[current_quantity_index]))
            current_quantity_index += 1
            
            menu_item = get_menu_item(food_item)
            if not menu_item:
                return create_response(
                    f"I'm sorry, we don't have {food_item} on our menu.",
                    session_id
                )

            # Validate quantity for food items
            is_valid, validation_message, contexts = validate_order_quantity(
                menu_item["id"],
                "food",
                quantity,
                session_id,
                project_id
            )
            
            if not is_valid:
                return create_response(validation_message, session_id, contexts)
                
            # Calculate total
            item_total, _ = calculate_item_total(menu_item, quantity)
            
            # Create order item
            order_item = {
                "item_id": menu_item["id"],
                "name": menu_item["name"],
                "quantity": quantity,
                "base_price": menu_item["base_price"],
                "customizations": [],  # No customizations in combined order yet
                "item_total": item_total
            }
            
            active_sessions[session_id]["items"].append(order_item)
            active_sessions[session_id]["total_amount"] += item_total
            response_items.append(f"{quantity} {menu_item['name']}")
        
        # Process drink items
        for i, drink_item in enumerate(drink_items):
            quantity = int(float(quantities[current_quantity_index]))
            current_quantity_index += 1
            
            # Get size for this drink if available
            size = drink_sizes[i] if i < len(drink_sizes) else None
            
            menu_item = get_menu_item(drink_item)
            if not menu_item:
                return create_response(
                    f"I'm sorry, we don't have {drink_item} on our menu.",
                    session_id
                )

            # Validate quantity for drink items
            is_valid, validation_message, contexts = validate_order_quantity(
                menu_item["id"],
                "drink",
                quantity,
                session_id,
                project_id
            )
            
            if not is_valid:
                return create_response(validation_message, session_id, contexts)
                
            # Calculate total with size
            item_total, size_price = calculate_item_total(menu_item, quantity, size)
            
            # Create order item
            order_item = {
                "item_id": menu_item["id"],
                "name": menu_item["name"],
                "quantity": quantity,
                "base_price": menu_item["base_price"],
                "size": size,
                "size_price": size_price,
                "item_total": item_total
            }
            
            active_sessions[session_id]["items"].append(order_item)
            active_sessions[session_id]["total_amount"] += item_total
            response_items.append(f"{quantity} {size if size else ''} {menu_item['name']}")
            
            # If drink needs size but none specified
            if not size and menu_item.get("has_size", False):
                return create_response(
                    f"What size would you like for your {drink_item}?",
                    session_id
                )
        
        # Create response text
        if not response_items:
            return create_response(
                "I'm sorry, I didn't catch what items you wanted to order. Could you please repeat that?",
                session_id
            )
            
        response_text = "Okay, I've added "
        if len(response_items) == 1:
            response_text += response_items[0]
        elif len(response_items) == 2:
            response_text += f"{response_items[0]} and {response_items[1]}"
        else:
            response_text += ", ".join(response_items[:-1]) + f", and {response_items[-1]}"
        response_text += " to your order. Anything else?"
        
        return create_response(response_text, session_id)
        
    except Exception as e:
        logger.error(f"Error in handle_order_combined: {str(e)}", exc_info=True)
        raise

def handle_order_modify(data: dict, session_id: str):
    """Handles modifications to the last ordered item."""
    try:
        # Extract modification details
        parameters = data["queryResult"]["parameters"]
        modification_types = parameters.get("modification-type", [])
        food_components = parameters.get("food-components", [])

        # Check if there's an active order
        if not session_id in active_sessions or not active_sessions[session_id]["items"]:
            return create_response(
                "I don't see any active orders to modify. What would you like to order?",
                session_id
            )

        # Get the last ordered item
        last_item = active_sessions[session_id]["items"][-1]
        
        # Get the menu item details to validate modifications
        menu_item = get_menu_item(last_item["name"])
        if not menu_item:
            return create_response(
                f"I'm sorry, I'm having trouble modifying your {last_item['name']}.",
                session_id
            )

        # Ensure modification_types and food_components are lists
        if not isinstance(modification_types, list):
            modification_types = [modification_types]
        if not isinstance(food_components, list):
            food_components = [food_components]

        # Process each new customization
        new_customizations = []
        for mod_type, component in zip(modification_types, food_components):
            if mod_type and component:
                # Validate the customization
                is_valid, message = validate_customization(menu_item, mod_type, component)
                if not is_valid:
                    return create_response(message, session_id)

                # Format customization based on type
                if mod_type in ["no", "without"]:
                    new_customizations.append(f"no {component}")
                elif mod_type in ["extra", "add"]:
                    new_customizations.append(f"extra {component}")
                elif mod_type in ["light", "heavy"]:
                    new_customizations.append(f"{mod_type} {component}")

        # Add new customizations to existing ones
        last_item["customizations"].extend(new_customizations)

        # Create response text
        response_text = f"I've updated your {last_item['name']}"
        if new_customizations:
            response_text += f" with {', '.join(new_customizations)}"
        response_text += ". Would you like anything else?"

        return create_response(response_text, session_id)

    except Exception as e:
        logger.error(f"Error in handle_order_modify: {str(e)}", exc_info=True)
        raise

def handle_order_quantity(data: dict, session_id: str):
    """Handles updating the quantity of the last ordered item."""
    try:
        # Extract new quantity
        parameters = data["queryResult"]["parameters"]
        new_quantity_param = parameters.get("number")
        
        try:
            new_quantity = int(float(new_quantity_param))
        except (ValueError, TypeError):
            return create_response(
                "I'm sorry, I didn't catch how many you wanted. Could you please repeat that?",
                session_id
            )

        # Check if there's an active order
        if not session_id in active_sessions or not active_sessions[session_id]["items"]:
            return create_response(
                "I don't see any active orders to modify. What would you like to order?",
                session_id
            )

        # Get the last ordered item
        last_item = active_sessions[session_id]["items"][-1]
        
        # Extract project_id from session name for validation context
        project_id = data["session"].split('/')[1]
        
        # Validate the new quantity
        is_valid, validation_message, contexts = validate_order_quantity(
            last_item["item_id"],
            "food" if "size" not in last_item else "drink",
            new_quantity,
            session_id,
            project_id
        )
        
        if not is_valid:
            return create_response(validation_message, session_id, contexts)

        # Calculate old and new totals
        old_total = last_item["item_total"]
        
        # Calculate new item total based on whether it's a drink with size or not
        if "size" in last_item and "size_price" in last_item:
            new_item_total = (last_item["base_price"] + last_item["size_price"]) * new_quantity
        else:
            new_item_total = last_item["base_price"] * new_quantity

        # Update the session
        last_item["quantity"] = new_quantity
        last_item["item_total"] = new_item_total
        active_sessions[session_id]["total_amount"] = (
            active_sessions[session_id]["total_amount"] - old_total + new_item_total
        )

        # Create response text
        response_text = f"I've updated the quantity to {new_quantity} {last_item['name']}"
        if "size" in last_item and last_item["size"]:
            response_text = f"I've updated the quantity to {new_quantity} {last_item['size']} {last_item['name']}"
        
        if last_item.get("customizations"):
            response_text += f" with {', '.join(last_item['customizations'])}"
        response_text += ". Would you like anything else?"

        return create_response(response_text, session_id)

    except Exception as e:
        logger.error(f"Error in handle_order_quantity: {str(e)}", exc_info=True)
        raise

def validate_order_quantity(item_id: str, category: str, quantity: int, session_id: str, project_id: str):
    """
    Validates if the order quantity is within acceptable limits.
    Returns (is_valid: bool, message: str, contexts: List[dict])
    
    Parameters:
    - item_id: str - The ID of the item being ordered
    - category: str - The category of the item ("food" or "drink")
    - quantity: int - The quantity being ordered
    - session_id: str - The current session ID
    - project_id: str - The Dialogflow project ID
    """
    try:
        # Get config document from Firestore
        config_ref = db.collection('configs').document('order_limits')
        config_doc = config_ref.get()
        
        if not config_doc.exists:
            logger.warning("Order limits config not found, using default validation")
            return True, None, None
            
        config = config_doc.to_dict()
        category_limits = config.get('order_limits', {}).get(category, {})
        
        # Check item-specific limit first, then fall back to category default
        max_quantity = (
            category_limits.get('item_specific_limits', {}).get(item_id) or 
            category_limits.get('default_max_quantity', 999)
        )
        
        if quantity > max_quantity:
            message = config.get('order_limits', {}).get('messages', {}).get('exceed_limit')
            if not message:
                message = f"For orders of {quantity} items, please visit our counter for special handling. How else can I help you?"
                
            # Add output context for limit acknowledgment
            context = [{
                "name": f"projects/{project_id}/agent/sessions/{session_id}/contexts/awaiting-limit-acknowledgment",
                "lifespanCount": 1
            }]
            return False, message.format(quantity=quantity, item_name=item_id), context
            
        return True, None, None
        
    except Exception as e:
        logger.error(f"Error in validate_order_quantity: {str(e)}")
        # Fail safe - allow order to proceed if validation fails
        return True, None, None
    
def handle_order_limit_acknowledge(data: dict, session_id: str):
    """Handles customer acknowledgment after receiving order limit message."""
    try:
        return create_response(
            "You're welcome!",
            session_id
        )
    except Exception as e:
        logger.error(f"Error in handle_order_limit_acknowledge: {str(e)}", exc_info=True)
        raise

def handle_order_complete_acknowledge(data: dict, session_id: str):
    """Handles customer acknowledgment after order completion."""
    try:
        return create_response(
            "You're welcome! Have a great day!",
            session_id
        )
    except Exception as e:
        logger.error(f"Error in handle_order_complete_acknowledge: {str(e)}", exc_info=True)
        raise

def validate_customization(menu_item: dict, mod_type: str, component: str) -> tuple[bool, str]:
    """
    Validates if a customization is allowed for the menu item.
    
    Args:
        menu_item: The menu item dictionary from Firestore
        mod_type: The type of modification requested (no, extra, light, heavy)
        component: The component to be modified
        
    Returns:
        tuple[bool, str]: (is_valid, message)
    """
    try:
        # Check if item has customizations defined
        if "customizations" not in menu_item:
            return False, f"I'm sorry, {menu_item['name']} cannot be customized."

        customizations = menu_item["customizations"]
        
        # Validate based on modification type
        if mod_type in ["no", "without"]:
            if component not in customizations.get("removable", []):
                return False, f"I'm sorry, we cannot remove {component} from this item."
                
        elif mod_type in ["extra", "add"]:
            if component not in customizations.get("addable", []):
                return False, f"I'm sorry, we cannot add extra {component} to this item."
                
        elif mod_type in ["light", "heavy"]:
            if component not in customizations.get("modifiable", []):
                return False, f"I'm sorry, we cannot modify the amount of {component}."
                
        return True, "Valid customization"
        
    except Exception as e:
        logger.error(f"Error validating customization: {str(e)}")
        return False, "Sorry, there was an error processing your customization request."
    
def format_item_description(item):
    """
    Formats an item description including customizations for the fulfillment text.
    """
    description = f"{item['quantity']} {item['name']}"
    
    # Add size for drinks
    if "size" in item:
        description = f"{item['quantity']} {item['size']} {item['name']}"
    
    # Add customizations if present
    if item.get("customizations"):
        customization_text = ", ".join(item["customizations"])
        description += f" with {customization_text}"
    
    return description