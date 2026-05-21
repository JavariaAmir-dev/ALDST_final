import LoadingSpinner from "./LoadingSpinner.jsx";

export default function LoadingButton({ loading, children, className = "", ...props }) {
  return (
    <button className={`btn-primary ${className}`} disabled={loading || props.disabled} {...props}>
      {loading ? <LoadingSpinner label="Working" /> : children}
    </button>
  );
}
