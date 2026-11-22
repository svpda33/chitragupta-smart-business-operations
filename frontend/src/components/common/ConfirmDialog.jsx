import Modal from "./Modal";
import Button from "./Button";

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  variant = "danger",
  loading = false,
  errorMessage,
  onConfirm,
  onCancel,
}) {
  const handleClose = () => {
    if (!loading) onCancel?.();
  };

  return (
    <Modal
      open={open}
      title={title}
      onClose={handleClose}
      footer={
        <>
          <Button variant="secondary" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant={variant} onClick={() => onConfirm?.()} loading={loading}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-sm text-slate-700">{message}</p>
      {errorMessage ? (
        <p role="alert" className="mt-4 text-sm text-red-700">
          {errorMessage}
        </p>
      ) : null}
    </Modal>
  );
}
