from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def collect_kubernetes_snapshot(kubeconfig: str | None = None) -> dict[str, Any]:
    """Collect node and pod summary from a Kubernetes cluster."""
    try:
        from kubernetes import client, config
        from kubernetes.config.config_exception import ConfigException

        if kubeconfig:
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
                tmp.write(kubeconfig)
                tmp.flush()
                config.load_kube_config(config_file=tmp.name)
        else:
            try:
                config.load_incluster_config()
            except ConfigException:
                config.load_kube_config()

        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        pods = v1.list_pod_for_all_namespaces(watch=False)

        node_items = [
            {
                "name": node.metadata.name,
                "status": next(
                    (c.type for c in (node.status.conditions or []) if c.type == "Ready"),
                    "Unknown",
                ),
                "kubelet_version": node.status.node_info.kubelet_version if node.status.node_info else None,
            }
            for node in nodes.items[:20]
        ]
        pod_items = [
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "node": pod.spec.node_name,
            }
            for pod in pods.items[:50]
        ]
        return {
            "nodes": node_items,
            "pods": pod_items,
            "node_count": len(node_items),
            "pod_count": len(pod_items),
            "source": "kubernetes",
        }
    except Exception as exc:
        logger.warning("Kubernetes collection failed: %s", exc)
        return {
            "nodes": [{"name": "demo-node-1", "status": "Ready", "kubelet_version": "v1.29.0"}],
            "pods": [{"name": "demo-pod-api", "namespace": "default", "phase": "Running", "node": "demo-node-1"}],
            "node_count": 1,
            "pod_count": 1,
            "source": "kubernetes",
            "demo": True,
            "error": str(exc),
        }
