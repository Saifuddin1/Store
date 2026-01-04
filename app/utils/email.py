from flask_mail import Message
from flask import url_for, current_app
from app import mail
import threading

def send_email_async(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, body_html):
    msg = Message(
        subject=subject,
        sender="rajusaifuddinrs1@gmail.com",
        recipients=recipients,
    )
    msg.html = body_html

    # 🔥 Send email in background
    thread = threading.Thread(
        target=send_email_async,
        args=(current_app._get_current_object(), msg)
    )
    thread.start()


def send_order_cancellation_email(order, cancelled_items, reason=None):

    is_full_cancel = all(item.status == "CANCELLED" for item in order.items)

    subject = (
        f"Your Order #{order.id} Has Been Cancelled"
        if is_full_cancel
        else f"Update on Your Order #{order.id}"
    )

    title = "Order Cancelled" if is_full_cancel else "Partial Cancellation Notice"

    intro_text = (
        f"Your entire order <strong>#{order.id}</strong> has been cancelled."
        if is_full_cancel
        else f"Some items from your order <strong>#{order.id}</strong> have been cancelled. "
             f"The remaining items will be processed and delivered as usual."
    )

    recipients = [order.user.email]

    # ================= BUILD ITEM ROWS =================
    product_rows = ""
    for item in cancelled_items:
        product_rows += f"""
        <tr>
          <td>{item.product_name}</td>
          <td align="center">{item.qty}</td>
          <td align="right">₹{item.subtotal}</td>
        </tr>
        """

    total_html = (
        f"""
        <p>
          <strong>Total Amount:</strong> ₹{order.total_amount}
        </p>
        """
        if is_full_cancel
        else ""
    )

    # ================= EMAIL BODY =================
    body_html = f"""
    <html>
    <body>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td align="center">

            <table width="600" cellpadding="12" cellspacing="0" border="0">

              <tr>
                <td>
                  <h2>{title}</h2>
                </td>
              </tr>

              <tr>
                <td>
                  <p>Hello <strong>{order.user.email}</strong>,</p>

                  <p>{intro_text}</p>

                  <h4>Cancelled Items</h4>

                  <table width="100%" cellpadding="6" cellspacing="0" border="1">
                    <tr>
                      <th align="left">Product</th>
                      <th align="center">Qty</th>
                      <th align="right">Amount</th>
                    </tr>
                    {product_rows}
                  </table>

                  {total_html}

                  <p>
                    <strong>Reason:</strong><br>
                    {reason or "No specific reason provided."}
                  </p>

                  <p>
                    If you have any questions, please contact our support team.
                  </p>

                  <p>
                    Regards,<br>
                    <strong>My Store</strong>
                  </p>
                </td>
              </tr>

              <tr>
                <td>
                  <hr>
                  <p>This is an automated message. Please do not reply.</p>
                </td>
              </tr>

            </table>

          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    send_email(
        subject=subject,
        recipients=recipients,
        body_html=body_html
    )


def send_stock_available_email(user_email, product):
    subject = f"🎉 {product.name} is back in stock!"

    product_url = url_for(
        "main.product_detail",
        slug=product.slug,
        _external=True
    )

    body_html = f"""
        <html>
        <body>

        <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td align="center">

            <table width="600" cellpadding="12" cellspacing="0" border="0">

                <tr>
                <td>
                    <h2>🎉 Back in Stock!</h2>
                </td>
                </tr>

                <tr>
                <td>
                    <p>Hello,</p>

                    <p>
                    Great news! The product you were waiting for is now
                    <strong>back in stock</strong>.
                    </p>

                    <p>
                    <strong>🛍 Product:</strong> {product.name}<br>
                    <strong>💰 Price:</strong> ₹{product.final_price}
                    </p>

                    <p>
                    👉 <a href="{product_url}">
                        Click here to view the product
                    </a>
                    </p>

                    <p>
                    Hurry! Stock may sell out again.
                    </p>

                    <p>
                    Regards,<br>
                    <strong>{current_app.config.get("SITE_NAME", "My Store")}</strong>
                    </p>
                </td>
                </tr>

                <tr>
                <td>
                    <hr>
                    <p>
                    You received this email because you asked to be notified
                    when this product becomes available.
                    </p>
                </td>
                </tr>

            </table>

            </td>
        </tr>
        </table>

        </body>
        </html>
    """

    send_email(
        subject=subject,
        recipients=[user_email],
        body_html=body_html
    )