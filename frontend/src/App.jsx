import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import "./App.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const QUICK_PROMPTS = [
  "Do you have Nike Air Max 270 size 9 black?",
  "Add Nike Air Max 270 size 9 white to my Smart Cart",
  "I want to speak to a human about my order",
];

const NAV_ITEMS = [
  {
    key: "chat",
    label: "AI Assistant",
    icon: "✦",
  },
  {
    key: "smart-cart",
    label: "Smart Cart",
    icon: "◎",
  },
  {
    key: "orders",
    label: "My Orders",
    icon: "▣",
  },
  {
    key: "support",
    label: "Support",
    icon: "♡",
  },
];

function App() {
  const [activeTab, setActiveTab] =
    useState("chat");

  const [userId, setUserId] =
    useState(1001);

  const [backendStatus, setBackendStatus] =
    useState("unknown");

  // --------------------------------------------------
  // Product catalog
  // --------------------------------------------------

  const [products, setProducts] =
    useState([]);

  // --------------------------------------------------
  // Chat
  // --------------------------------------------------

  const [message, setMessage] =
    useState("");

  const [messages, setMessages] =
    useState([
      {
        role: "assistant",
        text:
          "Hi! I'm your intelligent retail assistant. " +
          "I can help you find products, check stock, " +
          "manage your Smart Cart and escalate support issues.",
      },
    ]);

  const [chatLoading, setChatLoading] =
    useState(false);

  const [chatError, setChatError] =
    useState("");

  const messagesEndRef = useRef(null);

  // --------------------------------------------------
  // Smart Cart
  // --------------------------------------------------

  const [smartCarts, setSmartCarts] =
    useState([]);

  const [cartLoading, setCartLoading] =
    useState(false);

  const [cartError, setCartError] =
    useState("");

  // --------------------------------------------------
  // Orders
  // --------------------------------------------------

  const [orders, setOrders] =
    useState([]);

  const [ordersLoading, setOrdersLoading] =
    useState(false);

  const [ordersError, setOrdersError] =
    useState("");

  // --------------------------------------------------
  // Support
  // --------------------------------------------------

  const [
    supportRequests,
    setSupportRequests,
  ] = useState([]);

  const [
    supportLoading,
    setSupportLoading,
  ] = useState(false);

  const [
    supportSubmitting,
    setSupportSubmitting,
  ] = useState(false);

  const [supportError, setSupportError] =
    useState("");

  const [
    supportSuccess,
    setSupportSuccess,
  ] = useState("");

  const [
    supportMessage,
    setSupportMessage,
  ] = useState("");

  const [
    supportReason,
    setSupportReason,
  ] = useState("HUMAN_ESCALATION");

  const [
    supportPriority,
    setSupportPriority,
  ] = useState("MEDIUM");

  // --------------------------------------------------
  // Product lookup
  // --------------------------------------------------

  const productMap = useMemo(() => {
    const map = {};

    products.forEach((product) => {
      map[product.product_id] = product;
    });

    return map;
  }, [products]);

  const getProduct = (productId) => {
    return productMap[productId] || null;
  };

  const getProductName = (productId) => {
    const product =
      getProduct(productId);

    if (!product) {
      return `Product #${productId}`;
    }

    const name =
      product.name ||
      `Product #${productId}`;

    const brand = product.brand;

    if (
      brand &&
      !name
        .toLowerCase()
        .includes(
          brand.toLowerCase()
        )
    ) {
      return `${brand} ${name}`;
    }

    return name;
  };

  // --------------------------------------------------
  // Helpers
  // --------------------------------------------------

  const getNumericUserId = () => {
    const numericUserId =
      Number(userId);

    if (
      !Number.isInteger(
        numericUserId
      ) ||
      numericUserId <= 0
    ) {
      return null;
    }

    return numericUserId;
  };


  const backendFetch = async (url, options) => {
    try {
      const response = await fetch(url, options);

      // Any HTTP response proves the backend is reachable.
      // Only an actual network/fetch failure means it is offline.
      setBackendStatus("online");

      return response;
    } catch (error) {
      setBackendStatus("offline");
      throw error;
    }
  };

  const formatPrice = (value) => {
    if (
      value === null ||
      value === undefined
    ) {
      return "Not set";
    }

    const number =
      Number(value);

    if (Number.isNaN(number)) {
      return String(value);
    }

    return `Rs. ${number.toLocaleString()}`;
  };

  const formatDate = (value) => {
    if (!value) {
      return "—";
    }

    const date =
      new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return value;
    }

    return date.toLocaleString(
      undefined,
      {
        dateStyle: "medium",
        timeStyle: "short",
      }
    );
  };

  const getStatusClass = (
    status
  ) => {
    return (
      "status-badge status-" +
      String(status || "")
        .toLowerCase()
        .replaceAll("_", "-")
    );
  };

  const getPriorityClass = (
    priority
  ) => {
    return (
      "priority-badge priority-" +
      String(priority || "")
        .toLowerCase()
    );
  };

  const formatReason = (reason) => {
    if (!reason) {
      return "General Support";
    }

    return reason
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      );
  };

  // --------------------------------------------------
  // Chat
  // --------------------------------------------------

  const sendMessage = async (
    event
  ) => {
    event.preventDefault();

    const trimmed =
      message.trim();

    if (
      !trimmed ||
      chatLoading
    ) {
      return;
    }

    const numericUserId =
      getNumericUserId();

    if (!numericUserId) {
      setChatError(
        "Please enter a valid User ID."
      );
      return;
    }

    setChatError("");

    setMessages(
      (previous) => [
        ...previous,
        {
          role: "user",
          text: trimmed,
        },
      ]
    );

    setMessage("");
    setChatLoading(true);

    try {
      const response =
        await backendFetch(
          `${API_BASE}/chat/`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              user_id:
                numericUserId,

              message: trimmed,
            }),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Assistant request failed."
        );
      }

      setBackendStatus("online");

      setMessages(
        (previous) => [
          ...previous,
          {
            role: "assistant",

            text:
              data.reply ||
              "The assistant returned no response.",
          },
        ]
      );

      setSmartCarts([]);
      setOrders([]);
      setSupportRequests([]);
    } catch (error) {
      setChatError(
        error.message
      );

      setMessages(
        (previous) => [
          ...previous,
          {
            role: "assistant",

            text:
              "I couldn't reach the retail assistant backend.",
          },
        ]
      );
    } finally {
      setChatLoading(false);
    }
  };

  const applyQuickPrompt = (
    prompt
  ) => {
    setMessage(prompt);
  };

  // --------------------------------------------------
  // Smart Cart
  // --------------------------------------------------

  const loadSmartCarts =
    async () => {
      const numericUserId =
        getNumericUserId();

      if (!numericUserId) {
        setCartError(
          "Please enter a valid User ID."
        );
        return;
      }

      setCartLoading(true);
      setCartError("");

      try {
        const response =
          await backendFetch(
            `${API_BASE}/smart-cart/user/${numericUserId}`
          );

        const data =
          await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
              "Failed to load Smart Carts."
          );
        }

        setBackendStatus(
          "online"
        );

        setSmartCarts(
          data.carts || []
        );
      } catch (error) {
        setCartError(
          error.message
        );
      } finally {
        setCartLoading(false);
      }
    };

  const cancelSmartCartItem =
    async (itemId) => {
      const confirmed =
        window.confirm(
          "Cancel this Smart Cart item?"
        );

      if (!confirmed) {
        return;
      }

      setCartError("");

      try {
        const response =
          await backendFetch(
            `${API_BASE}/smart-cart/items/${itemId}/cancel`,
            {
              method: "PATCH",
            }
          );

        const data =
          await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
              "Unable to cancel this item."
          );
        }

        setBackendStatus(
          "online"
        );

        await loadSmartCarts();
      } catch (error) {
        setCartError(
          error.message
        );
      }
    };

  // --------------------------------------------------
  // Orders
  // --------------------------------------------------

  const loadOrders = async () => {
    const numericUserId =
      getNumericUserId();

    if (!numericUserId) {
      setOrdersError(
        "Please enter a valid User ID."
      );
      return;
    }

    setOrdersLoading(true);
    setOrdersError("");

    try {
      const response =
        await backendFetch(
          `${API_BASE}/orders/${numericUserId}`
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to load orders."
        );
      }

      setBackendStatus("online");

      setOrders(
        data.orders || []
      );
    } catch (error) {
      setOrdersError(
        error.message
      );
    } finally {
      setOrdersLoading(false);
    }
  };

  // --------------------------------------------------
  // Support
  // --------------------------------------------------

  const loadSupportRequests =
    async () => {
      const numericUserId =
        getNumericUserId();

      if (!numericUserId) {
        setSupportError(
          "Please enter a valid User ID."
        );
        return;
      }

      setSupportLoading(true);
      setSupportError("");

      try {
        const response =
          await backendFetch(
            `${API_BASE}/support/${numericUserId}`
          );

        const data =
          await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
              "Failed to load support requests."
          );
        }

        setBackendStatus(
          "online"
        );

        setSupportRequests(
          data.requests || []
        );
      } catch (error) {
        setSupportError(
          error.message
        );
      } finally {
        setSupportLoading(false);
      }
    };

  const createSupportRequest =
    async (event) => {
      event.preventDefault();

      const numericUserId =
        getNumericUserId();

      if (!numericUserId) {
        setSupportError(
          "Please enter a valid User ID."
        );
        return;
      }

      const trimmed =
        supportMessage.trim();

      if (!trimmed) {
        setSupportError(
          "Please describe your issue."
        );
        return;
      }

      setSupportSubmitting(true);

      setSupportError("");
      setSupportSuccess("");

      try {
        const response =
          await backendFetch(
            `${API_BASE}/support/`,
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body: JSON.stringify({
                user_id:
                  numericUserId,

                message: trimmed,

                reason:
                  supportReason,

                priority:
                  supportPriority,
              }),
            }
          );

        const data =
          await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
              "Failed to create support request."
          );
        }

        setBackendStatus(
          "online"
        );

        const requestId =
          data.request
            ?.request_id;

        setSupportSuccess(
          requestId
            ? `Support request #${requestId} created successfully.`
            : "Support request created successfully."
        );

        setSupportMessage("");

        setSupportReason(
          "HUMAN_ESCALATION"
        );

        setSupportPriority(
          "MEDIUM"
        );

        await loadSupportRequests();
      } catch (error) {
        setSupportError(
          error.message
        );
      } finally {
        setSupportSubmitting(
          false
        );
      }
    };

  // --------------------------------------------------
  // Navigation
  // --------------------------------------------------

  const openTab = async (
    tab
  ) => {
    setActiveTab(tab);

    if (tab === "smart-cart") {
      await loadSmartCarts();
    }

    if (tab === "orders") {
      await loadOrders();
    }

    if (tab === "support") {
      await loadSupportRequests();
    }
  };

  // --------------------------------------------------
  // Effects
  // --------------------------------------------------

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_BASE}/products/`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            "Failed to load product catalog."
          );
        }

        return response.json();
      })
      .then((data) => {
        if (cancelled) {
          return;
        }

        const catalog =
          Array.isArray(data)
            ? data
            : data.products || [];

        setProducts(catalog);
        setBackendStatus("online");
      })
      .catch(() => {
        // Product names safely fall back to product IDs.
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current
      ?.scrollIntoView({
        behavior: "smooth",
      });
  }, [
    messages,
    chatLoading,
  ]);

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="app-shell">
      {/* =============================================
          SIDEBAR
      ============================================= */}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">
            ✦
          </div>

          <div>
            <h1>
              RetailAI
            </h1>

            <span>
              Smart Commerce
            </span>
          </div>
        </div>

        <div className="sidebar-label">
          Workspace
        </div>

        <nav className="side-nav">
          {NAV_ITEMS.map(
            (item) => (
              <button
                key={
                  item.key
                }
                className={
                  activeTab ===
                  item.key
                    ? "side-nav-item active"
                    : "side-nav-item"
                }
                onClick={() =>
                  openTab(
                    item.key
                  )
                }
              >
                <span className="nav-icon">
                  {
                    item.icon
                  }
                </span>

                <span>
                  {
                    item.label
                  }
                </span>

                {item.key ===
                  "smart-cart" &&
                  smartCarts.length >
                    0 && (
                    <span className="nav-count">
                      {
                        smartCarts.length
                      }
                    </span>
                  )}

                {item.key ===
                  "orders" &&
                  orders.length >
                    0 && (
                    <span className="nav-count">
                      {
                        orders.length
                      }
                    </span>
                  )}
              </button>
            )
          )}
        </nav>

        <div className="sidebar-bottom">
          <div className="system-card">
            <div className="system-status-line">
              <span
                className={
                  `status-dot ${backendStatus}`
                }
              />

              <span>
                {backendStatus ===
                "online"
                  ? "System Online"
                  : backendStatus ===
                    "offline"
                  ? "Backend Offline"
                  : "Checking System"}
              </span>
            </div>

            <small>
              Local AI + Secure
              Retail Backend
            </small>
          </div>
        </div>
      </aside>

      {/* =============================================
          MAIN
      ============================================= */}

      <div className="main-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              AGENTIC RETAIL
            </p>

            <h2>
              {activeTab ===
                "chat" &&
                "AI Shopping Assistant"}

              {activeTab ===
                "smart-cart" &&
                "Smart Cart"}

              {activeTab ===
                "orders" &&
                "Order History"}

              {activeTab ===
                "support" &&
                "Customer Support"}
            </h2>
          </div>

          <div className="topbar-actions">
            <div className="user-control">
              <span>
                Demo User
              </span>

              <input
                type="number"
                min="1"
                value={userId}
                onChange={(
                  event
                ) => {
                  setUserId(
                    event.target
                      .value
                  );

                  setSmartCarts(
                    []
                  );

                  setOrders([]);

                  setSupportRequests(
                    []
                  );

                  setCartError(
                    ""
                  );

                  setOrdersError(
                    ""
                  );

                  setSupportError(
                    ""
                  );
                }}
              />
            </div>

            <div className="avatar">
              U
            </div>
          </div>
        </header>

        <main className="content">
          {/* =========================================
              CHAT
          ========================================= */}

          {activeTab ===
            "chat" && (
            <div className="chat-layout">
              <section className="chat-panel">
                <div className="chat-intro">
                  <div className="ai-orb">
                    ✦
                  </div>

                  <div>
                    <span className="ai-label">
                      RETAIL AI
                    </span>

                    <h3>
                      How can I help
                      you shop today?
                    </h3>

                    <p>
                      Search products,
                      check availability,
                      create Smart Cart
                      rules or request
                      human support.
                    </p>
                  </div>
                </div>

                <div className="messages">
                  {messages.map(
                    (
                      item,
                      index
                    ) => (
                      <div
                        key={
                          index
                        }
                        className={
                          `message-row ${item.role}`
                        }
                      >
                        {item.role ===
                          "assistant" && (
                          <div className="message-avatar assistant-avatar">
                            ✦
                          </div>
                        )}

                        <div className="message-content">
                          <span className="message-author">
                            {item.role ===
                            "user"
                              ? "You"
                              : "Retail AI"}
                          </span>

                          <div className="message-bubble">
                            {
                              item.text
                            }
                          </div>
                        </div>

                        {item.role ===
                          "user" && (
                          <div className="message-avatar user-avatar">
                            U
                          </div>
                        )}
                      </div>
                    )
                  )}

                  {chatLoading && (
                    <div className="message-row assistant">
                      <div className="message-avatar assistant-avatar">
                        ✦
                      </div>

                      <div className="message-content">
                        <span className="message-author">
                          Retail AI
                        </span>

                        <div className="message-bubble typing-bubble">
                          <span />
                          <span />
                          <span />
                        </div>
                      </div>
                    </div>
                  )}

                  <div
                    ref={
                      messagesEndRef
                    }
                  />
                </div>

                {chatError && (
                  <div className="alert alert-error chat-alert">
                    {
                      chatError
                    }
                  </div>
                )}

                <div className="quick-prompts">
                  {QUICK_PROMPTS.map(
                    (
                      prompt
                    ) => (
                      <button
                        key={
                          prompt
                        }
                        onClick={() =>
                          applyQuickPrompt(
                            prompt
                          )
                        }
                      >
                        {prompt}
                      </button>
                    )
                  )}
                </div>

                <form
                  className="chat-composer"
                  onSubmit={
                    sendMessage
                  }
                >
                  <input
                    value={message}
                    onChange={(
                      event
                    ) =>
                      setMessage(
                        event
                          .target
                          .value
                      )
                    }
                    placeholder="Ask Retail AI anything..."
                  />

                  <button
                    type="submit"
                    disabled={
                      chatLoading
                    }
                    className="send-button"
                  >
                    <span>
                      Send
                    </span>

                    <span>
                      →
                    </span>
                  </button>
                </form>
              </section>

              <aside className="insight-panel">
                <div className="insight-header">
                  <span>
                    ✦
                  </span>

                  <div>
                    <h3>
                      Agent
                      Capabilities
                    </h3>

                    <p>
                      What this assistant
                      can do
                    </p>
                  </div>
                </div>

                <div className="capability-list">
                  <div className="capability">
                    <div className="capability-icon">
                      ⌕
                    </div>

                    <div>
                      <strong>
                        Product Discovery
                      </strong>

                      <p>
                        Search the catalog
                        using natural
                        language.
                      </p>
                    </div>
                  </div>

                  <div className="capability">
                    <div className="capability-icon">
                      ◉
                    </div>

                    <div>
                      <strong>
                        Live Inventory
                      </strong>

                      <p>
                        Check size, color
                        and branch stock.
                      </p>
                    </div>
                  </div>

                  <div className="capability">
                    <div className="capability-icon">
                      ◎
                    </div>

                    <div>
                      <strong>
                        Smart Cart
                      </strong>

                      <p>
                        Watch prices and
                        authorize automatic
                        purchases.
                      </p>
                    </div>
                  </div>

                  <div className="capability">
                    <div className="capability-icon">
                      ♡
                    </div>

                    <div>
                      <strong>
                        Human Support
                      </strong>

                      <p>
                        Escalate important
                        customer issues.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="security-note">
                  <div>
                    ✓
                  </div>

                  <p>
                    Purchases are
                    validated by the
                    backend before any
                    transaction is
                    executed.
                  </p>
                </div>
              </aside>
            </div>
          )}

          {/* =========================================
              SMART CART
          ========================================= */}

          {activeTab ===
            "smart-cart" && (
            <section>
              <div className="page-banner purple-banner">
                <div>
                  <span className="banner-kicker">
                    SMART AUTOMATION
                  </span>

                  <h3>
                    Your Smart Cart
                  </h3>

                  <p>
                    Monitor products,
                    price limits and
                    automatic purchase
                    authorization.
                  </p>
                </div>

                <button
                  className="glass-button"
                  onClick={
                    loadSmartCarts
                  }
                  disabled={
                    cartLoading
                  }
                >
                  {cartLoading
                    ? "Refreshing..."
                    : "↻ Refresh"}
                </button>
              </div>

              {cartError && (
                <div className="alert alert-error">
                  {
                    cartError
                  }
                </div>
              )}

              {cartLoading &&
                smartCarts.length ===
                  0 && (
                  <LoadingCard
                    text="Loading your Smart Cart..."
                  />
                )}

              {!cartLoading &&
                !cartError &&
                smartCarts.length ===
                  0 && (
                  <EmptyState
                    icon="◎"
                    title="Your Smart Cart is empty"
                    text="Ask Retail AI to add a product and create a price condition."
                    buttonText="Open AI Assistant"
                    onClick={() =>
                      openTab(
                        "chat"
                      )
                    }
                  />
                )}

              <div className="cart-grid">
                {smartCarts.map(
                  (
                    cartEntry
                  ) => {
                    const cart =
                      cartEntry.cart;

                    const items =
                      cartEntry.items ||
                      [];

                    return (
                      <article
                        className="premium-card cart-card"
                        key={
                          cart.cart_id
                        }
                      >
                        <div className="premium-card-header">
                          <div>
                            <div className="card-title-row">
                              <div className="card-icon purple-icon">
                                ◎
                              </div>

                              <div>
                                <h3>
                                  Smart
                                  Cart
                                </h3>

                                <p>
                                  Created{" "}
                                  {formatDate(
                                    cart.created_at
                                  )}
                                </p>
                              </div>
                            </div>
                          </div>

                          <span
                            className={
                              getStatusClass(
                                cart.status
                              )
                            }
                          >
                            {
                              cart.status
                            }
                          </span>
                        </div>

                        <div className="premium-card-body">
                          {items.length ===
                          0 ? (
                            <p className="muted">
                              No items in
                              this Smart
                              Cart.
                            </p>
                          ) : (
                            <div className="smart-item-list">
                              {items.map(
                                (
                                  item
                                ) => {
                                  const product =
                                    getProduct(
                                      item.product_id
                                    );

                                  return (
                                    <div
                                      className="smart-item"
                                      key={
                                        item.item_id
                                      }
                                    >
                                      <div className="product-row">
                                        <div className="product-avatar">
                                          {product?.brand
                                            ?.charAt(
                                              0
                                            )
                                            .toUpperCase() ||
                                            "P"}
                                        </div>

                                        <div className="product-info">
                                          <span className="product-brand">
                                            {product?.brand ||
                                              "Retail Product"}
                                          </span>

                                          <h4>
                                            {getProductName(
                                              item.product_id
                                            )}
                                          </h4>

                                          <p>
                                            {item.variant ||
                                              "Default variant"}

                                            {item.color
                                              ? ` • ${item.color}`
                                              : ""}
                                          </p>
                                        </div>

                                        <span
                                          className={
                                            getStatusClass(
                                              item.status
                                            )
                                          }
                                        >
                                          {
                                            item.status
                                          }
                                        </span>
                                      </div>

                                      <div className="metric-grid">
                                        <Metric
                                          label="Quantity"
                                          value={
                                            item.quantity
                                          }
                                        />

                                        <Metric
                                          label="Current Price"
                                          value={
                                            product
                                              ? formatPrice(
                                                  product.current_price
                                                )
                                              : "—"
                                          }
                                        />

                                        <Metric
                                          label="Maximum Price"
                                          value={formatPrice(
                                            item.maximum_price
                                          )}
                                        />

                                        <Metric
                                          label="Auto Buy"
                                          value={
                                            item.auto_buy_enabled
                                              ? "Enabled"
                                              : "Disabled"
                                          }
                                          highlight={
                                            item.auto_buy_enabled
                                          }
                                        />
                                      </div>

                                      <div className="authorization-row">
                                        <div
                                          className={
                                            item.purchase_authorized_at
                                              ? "authorization authorized"
                                              : "authorization"
                                          }
                                        >
                                          <span>
                                            {item.purchase_authorized_at
                                              ? "✓"
                                              : "—"}
                                          </span>

                                          <div>
                                            <strong>
                                              {item.purchase_authorized_at
                                                ? "Purchase authorized"
                                                : "No auto-purchase authorization"}
                                            </strong>

                                            <p>
                                              {item.purchase_authorized_at
                                                ? "The backend may execute a controlled purchase when all conditions are satisfied."
                                                : "This item will only be monitored."}
                                            </p>
                                          </div>
                                        </div>

                                        {[
                                          "WATCHING",
                                          "FAILED",
                                        ].includes(
                                          item.status
                                        ) && (
                                          <button
                                            className="danger-outline"
                                            onClick={() =>
                                              cancelSmartCartItem(
                                                item.item_id
                                              )
                                            }
                                          >
                                            Cancel
                                            Item
                                          </button>
                                        )}
                                      </div>
                                    </div>
                                  );
                                }
                              )}
                            </div>
                          )}
                        </div>
                      </article>
                    );
                  }
                )}
              </div>
            </section>
          )}

          {/* =========================================
              ORDERS
          ========================================= */}

          {activeTab ===
            "orders" && (
            <section>
              <div className="page-banner dark-banner">
                <div>
                  <span className="banner-kicker">
                    PURCHASE HISTORY
                  </span>

                  <h3>
                    My Orders
                  </h3>

                  <p>
                    Review purchases
                    created through the
                    controlled retail
                    workflow.
                  </p>
                </div>

                <button
                  className="glass-button"
                  onClick={
                    loadOrders
                  }
                  disabled={
                    ordersLoading
                  }
                >
                  {ordersLoading
                    ? "Refreshing..."
                    : "↻ Refresh"}
                </button>
              </div>

              {ordersError && (
                <div className="alert alert-error">
                  {
                    ordersError
                  }
                </div>
              )}

              {ordersLoading &&
                orders.length ===
                  0 && (
                  <LoadingCard
                    text="Loading your orders..."
                  />
                )}

              {!ordersLoading &&
                !ordersError &&
                orders.length ===
                  0 && (
                  <EmptyState
                    icon="▣"
                    title="No purchases yet"
                    text="Orders created by successful Smart Cart purchases will appear here."
                  />
                )}

              <div className="orders-grid">
                {orders.map(
                  (order) => {
                    const product =
                      getProduct(
                        order.product_id
                      );

                    return (
                      <article
                        className="premium-card order-card"
                        key={
                          order.order_id
                        }
                      >
                        <div className="premium-card-header">
                          <div>
                            <span className="order-number">
                              ORDER #
                              {
                                order.order_id
                              }
                            </span>

                            <h3>
                              {getProductName(
                                order.product_id
                              )}
                            </h3>

                            <p>
                              {formatDate(
                                order.created_at
                              )}
                            </p>
                          </div>

                          <span
                            className={
                              getStatusClass(
                                order.status
                              )
                            }
                          >
                            {
                              order.status
                            }
                          </span>
                        </div>

                        <div className="premium-card-body">
                          <div className="order-product">
                            <div className="order-product-avatar">
                              {product?.brand
                                ?.charAt(
                                  0
                                )
                                .toUpperCase() ||
                                "P"}
                            </div>

                            <div>
                              <span>
                                {product?.brand ||
                                  "Product"}
                              </span>

                              <strong>
                                {getProductName(
                                  order.product_id
                                )}
                              </strong>

                              <p>
                                {order.variant ||
                                  "Default variant"}

                                {order.color
                                  ? ` • ${order.color}`
                                  : ""}
                              </p>
                            </div>
                          </div>

                          <div className="order-summary">
                            <div>
                              <span>
                                Quantity
                              </span>

                              <strong>
                                {
                                  order.quantity
                                }
                              </strong>
                            </div>

                            <div>
                              <span>
                                Purchase
                                Price
                              </span>

                              <strong className="price-value">
                                {formatPrice(
                                  order.price
                                )}
                              </strong>
                            </div>
                          </div>
                        </div>
                      </article>
                    );
                  }
                )}
              </div>
            </section>
          )}

          {/* =========================================
              SUPPORT
          ========================================= */}

          {activeTab ===
            "support" && (
            <section>
              <div className="page-banner blue-banner">
                <div>
                  <span className="banner-kicker">
                    HUMAN ASSISTANCE
                  </span>

                  <h3>
                    Support Center
                  </h3>

                  <p>
                    Create, review and
                    track issues that
                    require human
                    attention.
                  </p>
                </div>

                <button
                  className="glass-button"
                  onClick={
                    loadSupportRequests
                  }
                  disabled={
                    supportLoading
                  }
                >
                  {supportLoading
                    ? "Refreshing..."
                    : "↻ Refresh"}
                </button>
              </div>

              <div className="support-layout">
                <article className="premium-card support-form-card">
                  <div className="premium-card-header">
                    <div>
                      <span className="section-kicker">
                        NEW REQUEST
                      </span>

                      <h3>
                        How can we help?
                      </h3>

                      <p>
                        Send your issue
                        to the human
                        support queue.
                      </p>
                    </div>
                  </div>

                  <form
                    className="support-form"
                    onSubmit={
                      createSupportRequest
                    }
                  >
                    <div className="form-group">
                      <label>
                        Issue Type
                      </label>

                      <select
                        value={
                          supportReason
                        }
                        onChange={(
                          event
                        ) =>
                          setSupportReason(
                            event
                              .target
                              .value
                          )
                        }
                      >
                        <option value="HUMAN_ESCALATION">
                          General
                          Support
                        </option>

                        <option value="ORDER_ISSUE">
                          Order Issue
                        </option>

                        <option value="PAYMENT_OR_REFUND">
                          Payment or
                          Refund
                        </option>

                        <option value="PAYMENT_SECURITY">
                          Payment
                          Security
                        </option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>
                        Priority
                      </label>

                      <div className="priority-options">
                        {[
                          "LOW",
                          "MEDIUM",
                          "HIGH",
                          "URGENT",
                        ].map(
                          (
                            priority
                          ) => (
                            <button
                              type="button"
                              key={
                                priority
                              }
                              className={
                                supportPriority ===
                                priority
                                  ? `priority-option selected ${priority.toLowerCase()}`
                                  : "priority-option"
                              }
                              onClick={() =>
                                setSupportPriority(
                                  priority
                                )
                              }
                            >
                              {
                                priority
                              }
                            </button>
                          )
                        )}
                      </div>
                    </div>

                    <div className="form-group">
                      <label>
                        Describe your
                        issue
                      </label>

                      <textarea
                        rows="6"
                        placeholder="Tell us what happened..."
                        value={
                          supportMessage
                        }
                        onChange={(
                          event
                        ) =>
                          setSupportMessage(
                            event
                              .target
                              .value
                          )
                        }
                      />
                    </div>

                    {supportError && (
                      <div className="alert alert-error compact-alert">
                        {
                          supportError
                        }
                      </div>
                    )}

                    {supportSuccess && (
                      <div className="alert alert-success">
                        {
                          supportSuccess
                        }
                      </div>
                    )}

                    <button
                      type="submit"
                      className="primary-action"
                      disabled={
                        supportSubmitting
                      }
                    >
                      {supportSubmitting
                        ? "Submitting..."
                        : "Create Support Request →"}
                    </button>
                  </form>
                </article>

                <div className="support-history">
                  <div className="history-heading">
                    <div>
                      <span className="section-kicker">
                        REQUEST HISTORY
                      </span>

                      <h3>
                        My Requests
                      </h3>
                    </div>

                    <span className="history-count">
                      {
                        supportRequests.length
                      }
                    </span>
                  </div>

                  {supportLoading &&
                    supportRequests.length ===
                      0 && (
                      <LoadingCard
                        text="Loading support requests..."
                      />
                    )}

                  {!supportLoading &&
                    supportRequests.length ===
                      0 && (
                      <EmptyState
                        compact
                        icon="♡"
                        title="No support requests"
                        text="Requests created manually or by Retail AI will appear here."
                      />
                    )}

                  <div className="support-list">
                    {supportRequests.map(
                      (
                        request
                      ) => (
                        <article
                          className="support-ticket"
                          key={
                            request.request_id
                          }
                        >
                          <div className="ticket-top">
                            <div>
                              <span className="ticket-number">
                                #
                                {
                                  request.request_id
                                }
                              </span>

                              <strong>
                                {formatReason(
                                  request.reason
                                )}
                              </strong>
                            </div>

                            <span
                              className={
                                getStatusClass(
                                  request.status
                                )
                              }
                            >
                              {
                                request.status
                              }
                            </span>
                          </div>

                          <p className="ticket-message">
                            {
                              request.message
                            }
                          </p>

                          <div className="ticket-footer">
                            <span
                              className={
                                getPriorityClass(
                                  request.priority
                                )
                              }
                            >
                              {
                                request.priority
                              }
                            </span>

                            <span>
                              {formatDate(
                                request.created_at ||
                                  request.timestamp
                              )}
                            </span>
                          </div>

                          {request.resolution && (
                            <div className="resolution-box">
                              <strong>
                                Resolution
                              </strong>

                              <p>
                                {
                                  request.resolution
                                }
                              </p>
                            </div>
                          )}
                        </article>
                      )
                    )}
                  </div>
                </div>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

// --------------------------------------------------
// Reusable UI
// --------------------------------------------------

function Metric({
  label,
  value,
  highlight = false,
}) {
  return (
    <div className="metric">
      <span>
        {label}
      </span>

      <strong
        className={
          highlight
            ? "highlight-value"
            : ""
        }
      >
        {value}
      </strong>
    </div>
  );
}

function LoadingCard({
  text,
}) {
  return (
    <div className="loading-card">
      <div className="loader" />

      <span>
        {text}
      </span>
    </div>
  );
}

function EmptyState({
  icon,
  title,
  text,
  buttonText,
  onClick,
  compact = false,
}) {
  return (
    <div
      className={
        compact
          ? "empty-state compact"
          : "empty-state"
      }
    >
      <div className="empty-icon">
        {icon}
      </div>

      <h3>
        {title}
      </h3>

      <p>
        {text}
      </p>

      {buttonText && (
        <button
          onClick={onClick}
          className="empty-action"
        >
          {buttonText}
        </button>
      )}
    </div>
  );
}

export default App;