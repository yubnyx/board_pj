// 백엔드(FastAPI)와 통신하는 함수 모음.
// vite.config.js의 proxy 덕분에 "/api"로 보내면 localhost:8000으로 전달됩니다.

const BASE = "/api/posts";

async function handle(res) {
  if (!res.ok) {
    // 백엔드가 보내는 에러 메시지를 최대한 그대로 보여줍니다.
    let message = `요청 실패 (HTTP ${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) message = JSON.stringify(data.detail);
    } catch (_) {
      // 본문이 없으면(예: 204) 그냥 넘어감
    }
    throw new Error(message);
  }
  if (res.status === 204) return null; // 삭제 등 본문 없는 응답
  return res.json();
}

export function getPosts(page = 1, limit = 10) {
  // 페이지네이션: 응답은 { items, total, skip, limit } 형태
  const skip = (page - 1) * limit;
  return fetch(`${BASE}?skip=${skip}&limit=${limit}`).then(handle);
}

export function getPost(id) {
  return fetch(`${BASE}/${id}`).then(handle);
}

export function createPost(post) {
  return fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(post),
  }).then(handle);
}

export function updatePost(id, post) {
  return fetch(`${BASE}/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(post),
  }).then(handle);
}

export function deletePost(id) {
  return fetch(`${BASE}/${id}`, { method: "DELETE" }).then(handle);
}

// ───── 댓글 ─────
export function getComments(postId) {
  return fetch(`${BASE}/${postId}/comments`).then(handle);
}

export function createComment(postId, comment) {
  return fetch(`${BASE}/${postId}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(comment),
  }).then(handle);
}

export function deleteComment(commentId) {
  return fetch(`/api/comments/${commentId}`, { method: "DELETE" }).then(handle);
}

export function searchSemantic(query){
  return fetch(`/api/search?q=${encodeURIComponent(query)}`).then(handle);
}
