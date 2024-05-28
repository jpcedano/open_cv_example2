import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Int32
import cv2
import numpy as np

class WebcamSubscriber(Node):
    def __init__(self):
        super().__init__('webcam_subscriber')
        print("Initializing webcam subscriber node...")
        self.subscription = self.create_subscription(Image, '/video_source/raw', self.image_callback, 10)
        print("Subscription created.")
        self.publisher = self.create_publisher(Image, '/webcam_image', 10)
        print("Image publisher created.")
        self.signal_publisher = self.create_publisher(Int32, '/traffic_light_signal', 10)
        print("Signal publisher created.")

    def image_callback(self, msg):
        print("Received image message.")
        # Convertir la imagen recibida a un formato que OpenCV pueda manejar
        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, 3))
        
        # Procesar la imagen y publicarla
        processed_frame, signal_value = self.detect_and_highlight_circles(frame)
        self.publish_image(processed_frame)
        self.publish_signal(signal_value)

        # Mostrar la imagen procesada en una ventana de OpenCV
        cv2.namedWindow('Processed Image', cv2.WINDOW_NORMAL)  # Resizeable window
        cv2.imshow('Processed Image', processed_frame)
        cv2.waitKey(1)

    def publish_image(self, frame):
        print("Publishing image...")
        # Crear un mensaje Image a partir de la imagen procesada y publicarlo
        msg = Image()
        msg.height, msg.width, _ = frame.shape
        msg.encoding = 'bgr8'
        msg.data = frame.tobytes()
        self.publisher.publish(msg)

    def publish_signal(self, signal_value):
        print("Publishing signal value...")
        # Publicar el valor de la señal del semáforo
        msg = Int32()
        msg.data = signal_value
        self.signal_publisher.publish(msg)

    def detect_and_highlight_circles(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.medianBlur(gray, 11)

        color = (0, 0, 0)
        signal_value = 0

        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                                   param1=50, param2=30, minRadius=5, maxRadius=30)

        if circles is not None and len(circles[0]) > 0:
            filtered_circles = []
            for circle in circles[0]:
                x, y, r = circle
                circle_area = frame[int(y) - int(r):int(y) + int(r), int(x) - int(r):int(x) + int(r)]
                if np.any(circle_area):
                    hsv_circle = cv2.cvtColor(circle_area, cv2.COLOR_BGR2HSV)
                    mean_hsv = np.mean(hsv_circle, axis=(0, 1))
                    if (0 <= mean_hsv[0] < 30 or 160 <= mean_hsv[0] <= 180) or \
                       (35 <= mean_hsv[0] <= 55) or (60 <= mean_hsv[0] <= 85):
                        filtered_circles.append(circle)

            if len(filtered_circles) > 0:
                circle = filtered_circles[0]
                x, y, r = np.round(circle[0]), np.round(circle[1]), np.round(circle[2])

                circle_area = frame[int(y) - int(r):int(y) + int(r), int(x) - int(r):int(x) + int(r)]
                hsv_circle = cv2.cvtColor(circle_area, cv2.COLOR_BGR2HSV)
                mean_hsv = np.mean(hsv_circle, axis=(0, 1))

                if 0 <= mean_hsv[0] < 30 or 160 <= mean_hsv[0] <= 180:
                    color = (0, 0, 255)
                    signal_value = 3
                    print("Rojo Detectado")
                elif 35 <= mean_hsv[0] <= 55:
                    color = (0, 255, 255)
                    signal_value = 2
                    print("Amarillo Detectado")
                elif 60 <= mean_hsv[0] <= 85:
                    color = (0, 255, 0)
                    signal_value = 1
                    print("Verde Detectado")

                cv2.circle(frame, (int(x), int(y)), int(r), color, 2)
                cv2.rectangle(frame, (int(x) - int(r), int(y) - int(r)), (int(x) + int(r), int(y) + int(r)), color, 2)

                if color in [(0, 0, 255), (0, 255, 255), (0, 255, 0)]:
                    cv2.putText(frame, f"Semaforo en", (int(x) - int(r), int(y) - int(r) - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        else:
            print("Nothing detected")

        return frame, signal_value

def main(args=None):
    rclpy.init(args=args)
    webcam_subscriber = WebcamSubscriber()
    rclpy.spin(webcam_subscriber)
    webcam_subscriber.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
