import { useEffect, useState } from "react";
import {
  Link,
  Route,
  Routes,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";

import {
  createComment,
  createPost,
  deleteComment,
  deletePost,
  getComments,
  getPost,
  getPosts,
  searchSemantic,
  updatePost,
} from "./api.js";

// 날짜를 보기 좋게 (예: 2026-06-04 15:04)
function formatDate(value) {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16);
}

// ─────────────────────────────────────────────
// 글 목록 화면  (주소: / )
// ─────────────────────────────────────────────
const TYPE_LABEL = { title: "제목", content: "내용", comment: "댓글" };

const PAGE_SIZE = 10;

function PostList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // 주소 파라미터: ?q=... → AI 의미검색,  ?page=N → 일반 목록 페이지
  const aiQuery = searchParams.get("q") || "";
  const page = Number(searchParams.get("page") || 1);

  const [text, setText] = useState(aiQuery);
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [aiResults, setAiResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 주소가 바뀔 때마다 (검색/페이지/뒤로가기/새로고침) 데이터 다시 불러옴
  useEffect(() => {
    setText(aiQuery);
    setLoading(true);
    setError(null);
    if (aiQuery) {
      searchSemantic(aiQuery)
        .then(setAiResults)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    } else {
      getPosts(page, PAGE_SIZE)
        .then((res) => {
          setPosts(res.items);
          setTotal(res.total);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [aiQuery, page]);

  function onSearch(e) {
    e.preventDefault();
    const q = text.trim();
    setSearchParams(q ? { q } : {});
  }

  function goToPage(p) {
    setSearchParams(p === 1 ? {} : { page: String(p) });
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <div className="toolbar">
        <h1>게시판</h1>
        <button className="primary" onClick={() => navigate("/write")}>
          글쓰기
        </button>
      </div>

      <form className="search-bar" onSubmit={onSearch}>
        <input
          placeholder=" "
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button type="submit">검색</button>
        {aiQuery && (
          <button type="button" onClick={() => setSearchParams({})}>
            전체보기
          </button>
        )}
      </form>

      {aiQuery && (
        <p className="muted search-info">
          🤖 "{aiQuery}" 검색 결과 {aiResults.length}건
        </p>
      )}

      {loading ? (
        <p className="muted">불러오는 중…</p>
      ) : error ? (
        <p className="error">에러: {error}</p>
      ) : aiQuery ? (
        aiResults.length === 0 ? (
          <p className="muted">관련 글을 찾을 수 없어요. 다른 단어로 시도해보세요.</p>
        ) : (
          <ul className="ai-results">
            {aiResults.map((r) => (
              <li
                key={r.post_id}
                className="ai-result"
                onClick={() => navigate(`/posts/${r.post_id}`)}
              >
                <div className="ai-result-head">
                  <span className="ai-title">{r.post_title}</span>
                  <span className="ai-score">
                    관련도 {Math.round(r.top_score * 100)}%
                  </span>
                </div>
                <div className="ai-badges">
                  {r.matched_in.map((t) => (
                    <span key={t} className={`badge badge-${t}`}>
                      🏷 {TYPE_LABEL[t]}에서
                    </span>
                  ))}
                </div>
                {r.snippets.map((s, i) => (
                  <p key={i} className="ai-snippet">
                    "{s}"
                  </p>
                ))}
              </li>
            ))}
          </ul>
        )
      ) : posts.length === 0 ? (
        <p className="muted">아직 글이 없어요. 첫 글을 써보세요!</p>
      ) : (
        <>
          <table className="list">
            <thead>
              <tr>
                <th className="col-id">번호</th>
                <th>제목</th>
                <th className="col-author">작성자</th>
                <th className="col-date">작성일</th>
              </tr>
            </thead>
            <tbody>
              {posts.map((p) => (
                <tr key={p.id} onClick={() => navigate(`/posts/${p.id}`)}>
                  <td className="col-id">{p.id}</td>
                  <td className="title-cell">{p.title}</td>
                  <td className="col-author">{p.author}</td>
                  <td className="col-date">{formatDate(p.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} totalPages={totalPages} onChange={goToPage} />
        </>
      )}
    </div>
  );
}

// 페이지 번호 버튼들
function Pagination({ page, totalPages, onChange }) {
  if (totalPages <= 1) return null;
  return (
    <div className="pagination">
      <button disabled={page === 1} onClick={() => onChange(page - 1)}>
        이전
      </button>
      {[...Array(totalPages)].map((_, i) => {
        const n = i + 1;
        return (
          <button
            key={n}
            className={page === n ? "current" : ""}
            onClick={() => onChange(n)}
          >
            {n}
          </button>
        );
      })}
      <button
        disabled={page === totalPages}
        onClick={() => onChange(page + 1)}
      >
        다음
      </button>
    </div>
  );
}

// ─────────────────────────────────────────────
// 글 상세 화면  (주소: /posts/:id )
// ─────────────────────────────────────────────
function PostDetail() {
  const { id } = useParams(); // 주소 /posts/7 에서 7을 꺼냄
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getPost(id)
      .then(setPost)
      .catch((e) => setError(e.message));
  }, [id]);

  async function handleDelete() {
    if (!window.confirm("정말 삭제할까요?")) return;
    try {
      await deletePost(id);
      navigate("/"); // 삭제 후 목록으로
    } catch (e) {
      alert("삭제 실패: " + e.message);
    }
  }

  if (error) return <p className="error">에러: {error}</p>;
  if (!post) return <p className="muted">불러오는 중…</p>;

  return (
    <article className="detail">
      <h1>{post.title}</h1>
      <div className="meta">
        <span>작성자: {post.author}</span>
        <span>작성: {formatDate(post.created_at)}</span>
        {post.updated_at !== post.created_at && (
          <span>수정: {formatDate(post.updated_at)}</span>
        )}
      </div>
      <div className="content">{post.content}</div>

      <div className="toolbar">
        <button onClick={() => navigate("/")}>목록</button>
        <div className="spacer" />
        <button onClick={() => navigate(`/posts/${id}/edit`)}>수정</button>
        <button className="danger" onClick={handleDelete}>
          삭제
        </button>
      </div>

      <Comments postId={id} />
    </article>
  );
}

// ─────────────────────────────────────────────
// 댓글 영역 (상세 화면 안에 들어감)
// ─────────────────────────────────────────────
function Comments({ postId }) {
  const [comments, setComments] = useState([]);
  const [form, setForm] = useState({ author: "", content: "" });
  const [error, setError] = useState(null);
  // 지금 어느 댓글에 답글을 다는 중인지 (댓글 id 또는 null)
  const [replyTo, setReplyTo] = useState(null);

  // 댓글 목록을 (다시) 불러오는 함수
  function load() {
    getComments(postId)
      .then(setComments)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    load();
  }, [postId]);

  // 평평한 댓글 목록을 부모/자식으로 분리
  const roots = comments.filter((c) => c.parent_id == null); // 일반 댓글
  const repliesOf = (parentId) =>
    comments.filter((c) => c.parent_id === parentId); // 그 댓글의 답글들

  async function submitComment(e) {
    e.preventDefault();
    setError(null);
    try {
      await createComment(postId, form); // parent_id 없음 → 일반 댓글
      setForm({ author: "", content: "" });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove(id) {
    if (!window.confirm("삭제할까요? (답글도 함께 삭제됩니다)")) return;
    try {
      await deleteComment(id);
      load();
    } catch (err) {
      alert("삭제 실패: " + err.message);
    }
  }

  return (
    <section className="comments">
      <h2>댓글 {comments.length}</h2>

      <ul className="comment-list">
        {roots.length === 0 && <li className="muted">첫 댓글을 남겨보세요.</li>}

        {roots.map((c) => (
          <li key={c.id} className="comment">
            <div className="comment-head">
              <strong>{c.author}</strong>
              <span className="muted">{formatDate(c.created_at)}</span>
              <button
                className="link-action"
                onClick={() => setReplyTo(replyTo === c.id ? null : c.id)}
              >
                답글
              </button>
              <button className="link-danger" onClick={() => remove(c.id)}>
                삭제
              </button>
            </div>
            <div className="comment-body">{c.content}</div>

            {/* 답글 목록 (들여쓰기) */}
            {repliesOf(c.id).map((r) => (
              <div key={r.id} className="reply">
                <div className="comment-head">
                  <span className="reply-arrow">↳</span>
                  <strong>{r.author}</strong>
                  <span className="muted">{formatDate(r.created_at)}</span>
                  <button className="link-danger" onClick={() => remove(r.id)}>
                    삭제
                  </button>
                </div>
                <div className="comment-body">{r.content}</div>
              </div>
            ))}

            {/* 답글 입력칸 (답글 버튼 눌렀을 때만) */}
            {replyTo === c.id && (
              <ReplyForm
                postId={postId}
                parentId={c.id}
                onDone={() => {
                  setReplyTo(null);
                  load();
                }}
              />
            )}
          </li>
        ))}
      </ul>

      <form className="comment-form" onSubmit={submitComment}>
        <input
          placeholder="작성자"
          value={form.author}
          onChange={(e) => setForm({ ...form, author: e.target.value })}
          maxLength={100}
          required
        />
        <textarea
          placeholder="댓글을 입력하세요"
          value={form.content}
          onChange={(e) => setForm({ ...form, content: e.target.value })}
          rows={2}
          required
        />
        {error && <p className="error">에러: {error}</p>}
        <button type="submit" className="primary">
          댓글 등록
        </button>
      </form>
    </section>
  );
}

// 답글 입력 폼 (특정 댓글 밑에 뜸)
function ReplyForm({ postId, parentId, onDone }) {
  const [form, setForm] = useState({ author: "", content: "" });
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    try {
      // parent_id를 함께 보냄 → 답글로 저장됨
      await createComment(postId, { ...form, parent_id: parentId });
      onDone();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="comment-form reply-form" onSubmit={submit}>
      <input
        placeholder="작성자"
        value={form.author}
        onChange={(e) => setForm({ ...form, author: e.target.value })}
        maxLength={100}
        required
      />
      <textarea
        placeholder="답글을 입력하세요"
        value={form.content}
        onChange={(e) => setForm({ ...form, content: e.target.value })}
        rows={2}
        required
      />
      {error && <p className="error">에러: {error}</p>}
      <button type="submit" className="primary">
        답글 등록
      </button>
    </form>
  );
}

// ─────────────────────────────────────────────
// 글쓰기 / 수정 화면 (둘 다 같은 폼 사용)
//   글쓰기 주소: /write
//   수정   주소: /posts/:id/edit  (id가 있으면 수정 모드)
// ─────────────────────────────────────────────
function PostForm() {
  const { id: editId } = useParams(); // /write 면 undefined, /posts/7/edit 면 "7"
  const isEdit = editId != null;
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: "", content: "", author: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // 수정 모드면 기존 값을 불러와 폼을 채웁니다.
  useEffect(() => {
    if (isEdit) {
      getPost(editId)
        .then((p) =>
          setForm({ title: p.title, content: p.content, author: p.author })
        )
        .catch((e) => setError(e.message));
    }
  }, [editId, isEdit]);

  function change(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function submit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (isEdit) {
        await updatePost(editId, form);
        navigate(`/posts/${editId}`); // 수정 후 그 글 상세로
      } else {
        const created = await createPost(form);
        navigate(`/posts/${created.id}`); // 작성 후 새 글 상세로
      }
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  // 취소: 수정이면 상세로, 글쓰기면 목록으로
  function cancel() {
    navigate(isEdit ? `/posts/${editId}` : "/");
  }

  return (
    <form className="post-form" onSubmit={submit}>
      <h1>{isEdit ? "글 수정" : "글쓰기"}</h1>

      <label>
        제목
        <input
          name="title"
          value={form.title}
          onChange={change}
          maxLength={255}
          required
        />
      </label>

      <label>
        작성자
        <input
          name="author"
          value={form.author}
          onChange={change}
          maxLength={100}
          required
        />
      </label>

      <label>
        내용
        <textarea
          name="content"
          value={form.content}
          onChange={change}
          rows={10}
          required
        />
      </label>

      {error && <p className="error">에러: {error}</p>}

      <div className="toolbar">
        <button type="button" onClick={cancel}>
          취소
        </button>
        <div className="spacer" />
        <button type="submit" className="primary" disabled={submitting}>
          {submitting ? "저장 중…" : "저장"}
        </button>
      </div>
    </form>
  );
}

// ─────────────────────────────────────────────
// 전체 앱: 주소(URL) → 화면 연결표
// ─────────────────────────────────────────────
export default function App() {
  return (
    <div className="container">
      <Routes>
        <Route path="/" element={<PostList />} />
        <Route path="/write" element={<PostForm />} />
        <Route path="/posts/:id" element={<PostDetail />} />
        <Route path="/posts/:id/edit" element={<PostForm />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}

// 없는 주소로 들어왔을 때
function NotFound() {
  return (
    <div>
      <h1>페이지를 찾을 수 없어요</h1>
      <Link to="/">← 목록으로</Link>
    </div>
  );
}
