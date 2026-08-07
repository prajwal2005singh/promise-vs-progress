const API_BASE_URL = "http://127.0.0.1:8000";

function getToken() {
    return localStorage.getItem("token");
}

function getHeaders() {
    const headers = {
        "Content-Type": "application/json"
    };

    const token = getToken();

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
}