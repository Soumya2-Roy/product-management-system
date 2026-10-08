import os
import json
import gradio as gr
from groq import Groq

# ============================================================
# PRODUCT DATA
# Dictionary-based storage
# ============================================================

products = {
    101: {
        "name": "Laptop",
        "price": 55000.0,
        "quantity": 8,
        "category": "Electronics"
    },
    102: {
        "name": "Wireless Mouse",
        "price": 750.0,
        "quantity": 25,
        "category": "Accessories"
    },
    103: {
        "name": "Mechanical Keyboard",
        "price": 3200.0,
        "quantity": 12,
        "category": "Accessories"
    },
    104: {
        "name": "Monitor",
        "price": 14500.0,
        "quantity": 6,
        "category": "Electronics"
    }
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def next_product_id():
    if not products:
        return 1

    return max(products.keys()) + 1


def product_rows():
    rows = []

    for product_id, product in products.items():
        rows.append([
            product_id,
            product["name"],
            product["category"],
            product["price"],
            product["quantity"]
        ])

    return rows


def product_text():
    if not products:
        return "No products available."

    lines = []

    for product_id, product in products.items():
        lines.append(
            f"ID: {product_id} | "
            f"Name: {product['name']} | "
            f"Category: {product['category']} | "
            f"Price: ₹{product['price']:,.2f} | "
            f"Stock: {product['quantity']}"
        )

    return "\n".join(lines)


# ============================================================
# CRUD OPERATIONS
# ============================================================

def add_product(name, price, quantity, category):
    if not name or not name.strip():
        return "Product name is required.", product_rows()

    try:
        price = float(price)
        quantity = int(quantity)
    except (TypeError, ValueError):
        return "Price must be a number and quantity must be an integer.", product_rows()

    if price < 0:
        return "Price cannot be negative.", product_rows()

    if quantity < 0:
        return "Quantity cannot be negative.", product_rows()

    category = category.strip() if category else "General"

    product_id = next_product_id()

    products[product_id] = {
        "name": name.strip(),
        "price": price,
        "quantity": quantity,
        "category": category
    }

    return (
        f"Product added successfully. New Product ID: {product_id}",
        product_rows()
    )


def search_product(product_id, keyword):
    # Search by ID when an ID is supplied.
    if product_id not in (None, ""):
        try:
            product_id = int(product_id)
        except ValueError:
            return "Product ID must be an integer."

        if product_id in products:
            product = products[product_id]

            return (
                f"Product ID: {product_id}\n"
                f"Name: {product['name']}\n"
                f"Category: {product['category']}\n"
                f"Price: ₹{product['price']:,.2f}\n"
                f"Quantity: {product['quantity']}"
            )

        return "Product not found."

    # Otherwise search by name/category.
    if not keyword or not keyword.strip():
        return "Enter a Product ID or a search keyword."

    keyword = keyword.strip().lower()
    matches = []

    for product_id, product in products.items():
        if (
            keyword in product["name"].lower()
            or keyword in product["category"].lower()
        ):
            matches.append(
                f"ID: {product_id} | "
                f"{product['name']} | "
                f"{product['category']} | "
                f"₹{product['price']:,.2f} | "
                f"Stock: {product['quantity']}"
            )

    if not matches:
        return "No matching products found."

    return "\n".join(matches)


def update_product(product_id, name, price, quantity, category):
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return "Enter a valid Product ID.", product_rows()

    if product_id not in products:
        return "Product not found.", product_rows()

    if not name or not name.strip():
        return "Product name is required.", product_rows()

    try:
        price = float(price)
        quantity = int(quantity)
    except (TypeError, ValueError):
        return "Price must be a number and quantity must be an integer.", product_rows()

    if price < 0 or quantity < 0:
        return "Price and quantity cannot be negative.", product_rows()

    products[product_id] = {
        "name": name.strip(),
        "price": price,
        "quantity": quantity,
        "category": category.strip() if category else "General"
    }

    return "Product updated successfully.", product_rows()


def delete_product(product_id):
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return "Enter a valid Product ID.", product_rows()

    if product_id not in products:
        return "Product not found.", product_rows()

    deleted_name = products[product_id]["name"]
    del products[product_id]

    return f"Deleted: {deleted_name}", product_rows()


# ============================================================
# AI PRODUCT INSIGHTS
# ============================================================

def create_inventory_context():
    if not products:
        return "There are currently no products in the inventory."

    inventory = []

    for product_id, product in products.items():
        inventory.append({
            "id": product_id,
            "name": product["name"],
            "category": product["category"],
            "price": product["price"],
            "quantity": product["quantity"]
        })

    return json.dumps(inventory, indent=2)


def ai_product_assistant(user_question):
    if not user_question or not user_question.strip():
        return "Please enter a question."

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return (
            "GROQ_API_KEY is not configured.\n\n"
            "For Hugging Face Spaces, add GROQ_API_KEY in "
            "Settings → Secrets and variables → Secrets."
        )

    try:
        client = Groq(api_key=api_key)

        inventory = create_inventory_context()

        system_prompt = """
You are an inventory and product management assistant.

Use only the product inventory supplied by the application when making
claims about products, prices, stock, categories, or inventory totals.

You can:
- recommend products based on a user's requirements
- compare products
- identify low-stock items
- summarize inventory
- calculate simple inventory observations
- answer product-management questions

If the requested information is not available in the inventory, clearly
say that it is not available instead of inventing a product.

Keep responses practical and easy to understand.
"""

        user_prompt = f"""
Current inventory:

{inventory}

User question:
{user_question}
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=700
        )

        return response.choices[0].message.content

    except Exception as error:
        return f"AI service error: {error}"


# ============================================================
# DASHBOARD
# ============================================================

def inventory_summary():
    total_products = len(products)
    total_units = 0
    total_value = 0

    for product in products.values():
        total_units += product["quantity"]
        total_value += product["price"] * product["quantity"]

    low_stock = 0

    for product in products.values():
        if product["quantity"] <= 5:
            low_stock += 1

    return (
        f"Products: {total_products}   |   "
        f"Units: {total_units}   |   "
        f"Inventory Value: ₹{total_value:,.2f}   |   "
        f"Low Stock: {low_stock}"
    )


# ============================================================
# GRADIO APPLICATION
# ============================================================

custom_css = """
.gradio-container {
    max-width: 1200px !important;
}

.title {
    text-align: center;
}

.status-box textarea {
    font-size: 15px !important;
}
"""

with gr.Blocks(
    title="Smart Product Management System",
    css=custom_css,
    theme=gr.themes.Soft()
) as app:

    gr.Markdown(
        """
        # 🛒 Smart Product Management System
        ### Dictionary-based Inventory + AI Product Assistant
        """,
        elem_classes="title"
    )

    dashboard = gr.Markdown(inventory_summary())

    with gr.Tab("📦 Products"):

        gr.Markdown("### Current Inventory")

        product_table = gr.Dataframe(
            headers=[
                "Product ID",
                "Product Name",
                "Category",
                "Price",
                "Quantity"
            ],
            value=product_rows(),
            interactive=False
        )

        refresh_button = gr.Button("Refresh Inventory")

        refresh_button.click(
            inventory_summary,
            outputs=dashboard
        )

        refresh_button.click(
            product_rows,
            outputs=product_table
        )

        with gr.Row():

            with gr.Column():
                gr.Markdown("### Add Product")

                add_name = gr.Textbox(label="Product Name")
                add_price = gr.Number(label="Price")
                add_quantity = gr.Number(label="Quantity", precision=0)
                add_category = gr.Textbox(label="Category")

                add_button = gr.Button("Add Product", variant="primary")
                add_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    elem_classes="status-box"
                )

                add_button.click(
                    add_product,
                    inputs=[
                        add_name,
                        add_price,
                        add_quantity,
                        add_category
                    ],
                    outputs=[
                        add_status,
                        product_table
                    ]
                ).then(
                    inventory_summary,
                    outputs=dashboard
                )

            with gr.Column():
                gr.Markdown("### Search Product")

                search_id = gr.Textbox(
                    label="Product ID (optional)"
                )

                search_keyword = gr.Textbox(
                    label="Name or Category (optional)"
                )

                search_button = gr.Button("Search")

                search_result = gr.Textbox(
                    label="Search Result",
                    lines=8,
                    interactive=False
                )

                search_button.click(
                    search_product,
                    inputs=[
                        search_id,
                        search_keyword
                    ],
                    outputs=search_result
                )

    with gr.Tab("✏️ Update / Delete"):

        with gr.Row():

            with gr.Column():
                gr.Markdown("### Update Product")

                update_id = gr.Number(
                    label="Product ID",
                    precision=0
                )

                update_name = gr.Textbox(label="New Product Name")
                update_price = gr.Number(label="New Price")
                update_quantity = gr.Number(
                    label="New Quantity",
                    precision=0
                )
                update_category = gr.Textbox(
                    label="New Category"
                )

                update_button = gr.Button(
                    "Update Product",
                    variant="primary"
                )

                update_status = gr.Textbox(
                    label="Status",
                    interactive=False
                )

                update_button.click(
                    update_product,
                    inputs=[
                        update_id,
                        update_name,
                        update_price,
                        update_quantity,
                        update_category
                    ],
                    outputs=[
                        update_status,
                        product_table
                    ]
                ).then(
                    inventory_summary,
                    outputs=dashboard
                )

            with gr.Column():
                gr.Markdown("### Delete Product")

                delete_id = gr.Number(
                    label="Product ID",
                    precision=0
                )

                delete_button = gr.Button(
                    "Delete Product",
                    variant="stop"
                )

                delete_status = gr.Textbox(
                    label="Status",
                    interactive=False
                )

                delete_button.click(
                    delete_product,
                    inputs=delete_id,
                    outputs=[
                        delete_status,
                        product_table
                    ]
                ).then(
                    inventory_summary,
                    outputs=dashboard
                )

    with gr.Tab("🤖 AI Assistant"):

        gr.Markdown(
            """
            ### Ask questions about the current inventory

            Examples:
            - Which products are available below ₹5,000?
            - Which products have low stock?
            - Compare the laptop and monitor.
            - Recommend a product for a customer with a budget of ₹20,000.
            - Give me a short inventory summary.
            """
        )

        ai_question = gr.Textbox(
            label="Your Question",
            placeholder="Ask something about the products...",
            lines=4
        )

        ai_button = gr.Button(
            "Ask AI",
            variant="primary"
        )

        ai_answer = gr.Markdown()

        ai_button.click(
            ai_product_assistant,
            inputs=ai_question,
            outputs=ai_answer
        )

        gr.Markdown(
            """
            **API requirement:** Set the `GROQ_API_KEY` environment variable
            before using the AI Assistant.
            """
        )

    with gr.Tab("📊 Inventory Summary"):

        summary_button = gr.Button("Generate Summary")

        summary_output = gr.Textbox(
            label="Inventory Summary",
            lines=6,
            interactive=False
        )

        summary_button.click(
            inventory_summary,
            outputs=summary_output
        )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.launch(
        server_name="0.0.0.0",
        server_port=port
    )
