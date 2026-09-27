//
// FitBuddy WatchKit Extension: Bi-Directional Workout Session & HealthKit Tracker
// Collects continuous HR, active kilocalories, and streams telemetry via WCSession.
//

import WatchKit
import Foundation
import HealthKit
import WatchConnectivity

class WorkoutTrackingManager: NSObject, HKWorkoutSessionDelegate, HKLiveWorkoutBuilderDelegate, WCSessionDelegate {
    
    private let healthStore = HKHealthStore()
    private var workoutSession: HKWorkoutSession?
    private var workoutBuilder: HKLiveWorkoutBuilder?
    private var wcSession: WCSession?
    
    var currentHeartRate: Double = 0.0
    var activeCalories: Double = 0.0
    
    override init() {
        super.init()
        setupWatchConnectivity()
    }
    
    private func setupWatchConnectivity() {
        if WCSession.isSupported() {
            wcSession = WCSession.default
            wcSession?.delegate = self
            wcSession?.activate()
        }
    }
    
    func startWorkout() {
        let typesToShare: Set = [HKQuantityType.workoutType()]
        let typesToRead: Set = [
            HKQuantityType.quantityType(forIdentifier: .heartRate)!,
            HKQuantityType.quantityType(forIdentifier: .activeEnergyBurned)!
        ]
        
        healthStore.requestAuthorization(toShare: typesToShare, read: typesToRead) { (success, error) in
            guard success else { return }
            
            let configuration = HKWorkoutConfiguration()
            configuration.activityType = .traditionalStrengthTraining
            configuration.locationType = .indoor
            
            do {
                self.workoutSession = try HKWorkoutSession(healthStore: self.healthStore, configuration: configuration)
                self.workoutBuilder = self.workoutSession?.associatedWorkoutBuilder()
                
                self.workoutSession?.delegate = self
                self.workoutBuilder?.delegate = self
                
                self.workoutBuilder?.dataSource = HKLiveWorkoutDataSource(healthStore: self.healthStore, workoutConfiguration: configuration)
                
                self.workoutSession?.startActivity(with: Date())
                self.workoutBuilder?.beginCollection(withStart: Date()) { (success, error) in
                    print("Workout collection started successfully")
                }
            } catch {
                print("Failed to start workout session: \(error.localizedDescription)")
            }
        }
    }
    
    func workoutBuilder(_ workoutBuilder: HKLiveWorkoutBuilder, didCollectDataOf collectedTypes: Set<HKSampleType>) {
        for type in collectedTypes {
            guard let quantityType = type as? HKQuantityType else { continue }
            
            let statistics = workoutBuilder.statistics(for: quantityType)
            
            if quantityType == HKQuantityType.quantityType(forIdentifier: .heartRate) {
                let heartRateUnit = HKUnit.count().unitDivided(by: HKUnit.minute())
                if let value = statistics?.mostRecentQuantity()?.doubleValue(for: heartRateUnit) {
                    self.currentHeartRate = value
                    self.streamTelemetryToPhone(heartRate: value, calories: self.activeCalories)
                }
            } else if quantityType == HKQuantityType.quantityType(forIdentifier: .activeEnergyBurned) {
                let calUnit = HKUnit.kilocalorie()
                if let value = statistics?.sumQuantity()?.doubleValue(for: calUnit) {
                    self.activeCalories = value
                }
            }
        }
    }
    
    private func streamTelemetryToPhone(heartRate: Double, calories: Double) {
        guard let session = wcSession, session.isReachable else { return }
        let payload: [String: Any] = [
            "heart_rate": heartRate,
            "calories_burned": calories,
            "timestamp": Date().timeIntervalSince1970
        ]
        session.sendMessage(payload, replyHandler: nil, errorHandler: nil)
    }
    
    // MARK: - WCSessionDelegate Stubs
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {}
    func workoutSession(_ workoutSession: HKWorkoutSession, didChangeTo toState: HKWorkoutSessionState, from fromState: HKWorkoutSessionState, date: Date) {}
    func workoutSession(_ workoutSession: HKWorkoutSession, didFailWithError error: Error) {}
    func workoutBuilderDidCollectEvent(_ workoutBuilder: HKLiveWorkoutBuilder) {}
}
