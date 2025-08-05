const cart = {};

function loadStock() {
  fetch('/stock')
    .then(res => res.json())
    .then(stock => {
      const snackList = document.getElementById('snackList');
      snackList.innerHTML = '';

      for (const [snack, details] of Object.entries(stock)) {
        const disabled = details.stock === 0 ? 'disabled' : '';
        const allergies = details.allergies && details.allergies.length
          ? `Allergies: ${details.allergies.join(', ')}`
          : 'Allergies: None';

        snackList.innerHTML += `
          <div class="card">
            <h3>${snack}</h3>
            <p>Stock: ${details.stock}</p>
            <p style="color: red; font-weight: bold;">${allergies}</p>
            <button ${disabled} onclick="addToCart('${snack}')">Add to Cart</button>
          </div>
        `;
      }
    });
}

function addToCart(snack) {
  cart[snack] = (cart[snack] || 0) + 1;
  renderCart();
}

function removeFromCart(snack) {
  if (cart[snack]) {
    cart[snack]--;
    if (cart[snack] <= 0) {
      delete cart[snack];
    }
    renderCart();
  }
}

function renderCart() {
  const cartSummary = document.getElementById('cartSummary');
  cartSummary.innerHTML = '';

  const keys = Object.keys(cart);
  if (keys.length === 0) {
    cartSummary.innerHTML = '<p>No items in cart.</p>';
    document.getElementById('checkoutBtn').disabled = true;
    return;
  }

  keys.forEach(snack => {
    cartSummary.innerHTML += `
      <p>${snack} x ${cart[snack]} 
      <button onclick="removeFromCart('${snack}')">-</button></p>
    `;
  });

  document.getElementById('checkoutBtn').disabled = false;
}

function openCheckout() {
  const checkoutModal = document.getElementById('checkoutModal');
  const checkoutItems = document.getElementById('checkoutItems');
  checkoutItems.innerHTML = '';

  for (const snack in cart) {
    checkoutItems.innerHTML += `<p>${snack} x ${cart[snack]}</p>`;
  }

  document.getElementById('nameInput').value = '';
  document.getElementById('pickupMethod').value = 'Pickup';
  checkoutModal.classList.remove('hidden');
}

function closeCheckout() {
  document.getElementById('checkoutModal').classList.add('hidden');
}

function submitCheckout() {
  const name = document.getElementById('nameInput').value.trim();
  const pickupMethod = document.getElementById('pickupMethod').value;

  if (!name) {
    alert("Please enter your name or table.");
    return;
  }

  if (Object.keys(cart).length === 0) {
    alert("Your cart is empty.");
    return;
  }

  // Send entire cart in one request
  fetch('/order', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      cart: cart,
      name: name,
      pickup_method: pickupMethod
    })
  })
  .then(res => {
    if (!res.ok) {
      return res.json().then(data => Promise.reject(new Error(data.message || "Order failed")));
    }
    return res.json();
  })
  .then(() => {
    closeCheckout();
    document.getElementById('confirmation').classList.remove('hidden');
    setTimeout(() => {
      document.getElementById('confirmation').classList.add('hidden');
      loadStock();
    }, 3000);
    // Clear cart
    for (const key in cart) delete cart[key];
    renderCart();
  })
  .catch(err => {
    alert("Error placing order: " + err.message);
  });
}

document.getElementById('checkoutBtn').onclick = openCheckout;

window.onload = () => {
  loadStock();
  renderCart();
};
