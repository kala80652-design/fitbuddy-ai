/**
 * FitBuddy Edge Pose Tracking & Kinematic Joint Angle Calculation Engine
 * Uses MediaPipe Pose & HTML5 Canvas for real-time edge biomechanics & rep counting.
 */

class FitBuddyPoseTracker {
    constructor(videoElement, canvasElement, feedbackCallback) {
        this.videoElement = videoElement;
        this.canvasElement = canvasElement;
        this.canvasCtx = canvasElement.getContext('2d');
        this.feedbackCallback = feedbackCallback;
        
        this.repCount = 0;
        this.repStage = 'up'; // 'up' or 'down'
        this.currentAngle = 0;
        this.activeExercise = 'squat'; // Default
    }

    // Calculate the 2D planar angle formed by three keypoints (A -> B -> C)
    calculateAngle(pointA, pointB, pointC) {
        const radians = Math.atan2(pointC.y - pointB.y, pointC.x - pointB.x) -
                        Math.atan2(pointA.y - pointB.y, pointA.x - pointB.x);
        let angle = Math.abs(radians * (180.0 / Math.PI));
        if (angle > 180.0) {
            angle = 360.0 - angle;
        }
        return Math.round(angle);
    }

    processLandmarks(landmarks) {
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);

        // Draw video frame to canvas
        this.canvasCtx.drawImage(this.videoElement, 0, 0, this.canvasElement.width, this.canvasElement.height);

        if (!landmarks || landmarks.length === 0) return;

        // Extract key anatomical points
        // Left Side: Hip (23), Knee (25), Ankle (27), Shoulder (11), Elbow (13), Wrist (15)
        const leftHip = landmarks[23];
        const leftKnee = landmarks[25];
        const leftAnkle = landmarks[27];
        const leftShoulder = landmarks[11];
        const leftElbow = landmarks[13];
        const leftWrist = landmarks[15];

        let feedback = "Good posture. Maintain steady tempo.";

        if (this.activeExercise === 'squat' && leftHip && leftKnee && leftAnkle) {
            // Calculate Knee Flexion Angle
            const kneeAngle = this.calculateAngle(leftHip, leftKnee, leftAnkle);
            this.currentAngle = kneeAngle;

            // Rep Counting & Depth Evaluation Logic
            if (kneeAngle > 160) {
                this.repStage = 'up';
            }
            if (kneeAngle < 95 && this.repStage === 'up') {
                this.repStage = 'down';
                this.repCount += 1;
                feedback = " Excellent depth! Drive through midfoot.";
            } else if (kneeAngle >= 95 && kneeAngle < 130 && this.repStage === 'up') {
                feedback = " Squat deeper: Reach parallel (hip crease below knee).";
            }
        } else if (this.activeExercise === 'pushup' && leftShoulder && leftElbow && leftWrist) {
            // Calculate Elbow Flexion Angle
            const elbowAngle = this.calculateAngle(leftShoulder, leftElbow, leftWrist);
            this.currentAngle = elbowAngle;

            if (elbowAngle > 155) {
                this.repStage = 'up';
            }
            if (elbowAngle < 90 && this.repStage === 'up') {
                this.repStage = 'down';
                this.repCount += 1;
                feedback = " Full range achieved! Lock out at the top.";
            }
        }

        // Draw Skeletal Overlay Connections
        this.drawSkeleton(landmarks);

        // Trigger Real-Time Feedback Callback
        if (this.feedbackCallback) {
            this.feedbackCallback({
                exercise: this.activeExercise,
                reps: this.repCount,
                angle: this.currentAngle,
                stage: this.repStage,
                feedback: feedback
            });
        }
    }

    drawSkeleton(landmarks) {
        const ctx = this.canvasCtx;
        ctx.fillStyle = "#00f0ff";
        ctx.strokeStyle = "#39ff14";
        ctx.lineWidth = 4;

        // Draw Keypoint Nodes
        landmarks.forEach(point => {
            const x = point.x * this.canvasElement.width;
            const y = point.y * this.canvasElement.height;
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, 2 * Math.PI);
            ctx.fill();
        });
    }
}
