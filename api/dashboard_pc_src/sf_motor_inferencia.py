import cv2
import time
from ultralytics import YOLO

class MotorInferencia:
    def __init__(self, model_path="yolov8n.pt", conf_threshold=0.5):
        self.conf_threshold = float(conf_threshold)
        self.model_path = model_path
        self.model = None
        self.cargar_modelo(model_path)

    def cargar_modelo(self, model_path):
        """Carga o actualiza el modelo YOLO (.pt) en memoria."""
        try:
            print(f"[MotorIA] Cargando modelo YOLO desde: {model_path}")
            self.model = YOLO(model_path)
            self.model_path = model_path
            print("[MotorIA] Modelo cargado correctamente.")
            return True
        except Exception as e:
            print(f"[MotorIA] Error al cargar el modelo: {e}")
            return False

    def set_confianza(self, conf):
        """Ajusta el umbral de confianza en tiempo real."""
        self.conf_threshold = float(conf)
        print(f"[MotorIA] Umbral de confianza ajustado a: {self.conf_threshold}")

    def procesar_frame(self, frame):
        """Aplica inferencia sobre un frame y retorna la imagen anotada."""
        if self.model is None:
            return frame
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        return results[0].plot()

    def generar_frames(self, ip_robot="127.0.0.1", puerto=8080):
        """Consume el stream HTTP de la Raspberry Pi (/video_feed) y emite bytes JPEG."""
        stream_url = f"http://{ip_robot}:{puerto}/video_feed"
        print(f"[MotorIA] Conectando al stream en: {stream_url}")
        cap = cv2.VideoCapture(stream_url)
        
        while True:
            success, frame = cap.read()
            if not success:
                time.sleep(0.5)
                cap.open(stream_url)
                continue

            annotated_frame = self.procesar_frame(frame)
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        cap.release()

if __name__ == "__main__":
    import sys
    ip_test = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    puerto_test = sys.argv[2] if len(sys.argv) > 2 else "8080"
    motor = MotorInferencia(model_path="yolov8n.pt", conf_threshold=0.5)
    print(f"[TEST] Probando motor contra http://{ip_test}:{puerto_test}/video_feed")
    cap = cv2.VideoCapture(f"http://{ip_test}:{puerto_test}/video_feed")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("SafeVision - Test Motor Inferencia", motor.procesar_frame(frame))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
