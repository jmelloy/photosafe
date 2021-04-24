/*
See LICENSE folder for this sample’s licensing information.

Abstract:
Contains the sample's app delegate.
*/

import UIKit
import Photos
import BackgroundTasks

@UIApplicationMain
class AppDelegate: UIResponder, UIApplicationDelegate, UISplitViewControllerDelegate {
    
    var window: UIWindow?
    
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        guard let splitViewController = self.window?.rootViewController as? UISplitViewController else { return true }
        #if os(iOS)
        guard let navigationController = splitViewController.viewControllers.last as? UINavigationController else { return true }
        navigationController.topViewController!.navigationItem.leftBarButtonItem = splitViewController.displayModeButtonItem
        #endif
        splitViewController.delegate = self
        
        BGTaskScheduler.shared.register(forTaskWithIdentifier: "life.melloy.photosafe.sync", using: nil) { task in
            // Downcast the parameter to a processing task as this identifier is used for a processing request.
            self.handlePhotoSync(task: task as! BGProcessingTask)
        }

        startBackgroundTask()
        
        return true
    }
    
    func startBackgroundTask() {
        let request = BGProcessingTaskRequest(identifier: "life.melloy.photosafe.sync")
        request.requiresNetworkConnectivity = false
        request.requiresExternalPower = true
        
        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            print("Could not schedule background task: \(error)")
        }

    }
    
    func handlePhotoSync(task: BGProcessingTask) {
    
        let task = BGUpload()
        task.handlePhotoSync()
        
    }

    // MARK: Split view
    
    func splitViewController(_ splitViewController: UISplitViewController, collapseSecondary secondaryViewController: UIViewController,
                             onto primaryViewController: UIViewController) -> Bool {
        guard let secondaryAsNavController = secondaryViewController as? UINavigationController else { return false }
        guard let topAsDetailController = secondaryAsNavController.topViewController as? AssetGridViewController else { return false }
        if topAsDetailController.fetchResult == nil {
            // Return true to indicate that the app has handled the collapse by doing nothing and will discard the secondary controller.
            return true
        }
        return false
    }
    
    func splitViewController(_ splitViewController: UISplitViewController, showDetail viewController: UIViewController, sender: Any?) -> Bool {
        // Let the storyboard handle the segue for every case except going from detail:assetgrid to detail:asset.
        guard !splitViewController.isCollapsed else { return false }
        guard !(viewController is UINavigationController) else { return false }
        guard let detailNavController =
            splitViewController.viewControllers.last! as? UINavigationController,
            detailNavController.viewControllers.count == 1
            else { return false }
        
        detailNavController.pushViewController(viewController, animated: true)
        return true
    }
}
