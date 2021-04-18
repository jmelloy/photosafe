//
//  BGUpload.swift
//  PhotoBrowse iOS
//
//  Created by Jeffrey Melloy on 5/11/20.
//  Copyright © 2020 Apple. All rights reserved.
//

import Foundation
import Photos
import BackgroundTasks
import SQLite3
import UIKit

class BGUpload: NSObject, PHPhotoLibraryChangeObserver {
    var fetchResult: PHFetchResult<PHAsset>!
    var queue = OperationQueue()
    var db: OpaquePointer?
    let imageManager = PHCachingImageManager()
    
    override init() {
        super.init()
        
        PHPhotoLibrary.shared().register(self)
        
        self.db = openDatabase()
        
        createTable()
    }
    
    func handlePhotoSync() {
        if fetchResult == nil {
            let allPhotosOptions = PHFetchOptions()
            allPhotosOptions.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: true)]
            fetchResult = PHAsset.fetchAssets(with: allPhotosOptions)
        }

        for index in 0..<fetchResult.count {
            let asset = fetchResult.object(at: index)
            print(asset)
            let options = PHImageRequestOptions()
            
            imageManager.requestImage(for: asset,
                                      targetSize: PHImageManagerMaximumSize,
                                      contentMode: .aspectFill,
                                      options: options,
                                      resultHandler: {
                                               image, info in
                                                print(image)
                                                print(info)
                                        if let new_image = image {
                                            self.uploadPhoto(photo: new_image)
                                        }
                                                
                                      })
        }
        
    }
    
    func uploadPhoto(photo: UIImage) {
        let server = "http://localhost:8080"
        let session = URLSession(configuration: .default)
        
        if let url = URL(string: server) {
            
            var request = URLRequest(url: url)
            request.httpMethod = "POST"

            let boundary = UUID().uuidString
            
            request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

            var uploadTask: URLSessionUploadTask?
            
            if let data:Data = photo.jpegData(compressionQuality: 1.0) {
                print(data)
                request.addValue("image/jpeg", forHTTPHeaderField: "Content-Type")

                uploadTask = session.uploadTask(with: request, from: data, completionHandler: {
                    data, response, error in
                        print("Response \(response) - \(error)")
                })

            }
            uploadTask?.resume()

        }

    }
    
    func openDatabase() -> OpaquePointer? {
      var db: OpaquePointer?
      let fileURL = try! FileManager.default.url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: false)
        .appendingPathComponent("photos.sqlite")
        
        if sqlite3_open(fileURL.path, &db) == SQLITE_OK {
          print("Successfully opened connection to database at \(fileURL)")
          return db
        } else {
          print("Unable to open database.")
            return nil;
        }
    }

    func createTable() {
        let createTableString = """
        create table if not exists photos(
            uuid varchar,
            hidden boolean,
            width int,
            height int,
            location varchar,
            mediaType int
        );
        """
        var createTableStatement: OpaquePointer?
        // 2
        if sqlite3_prepare_v2(db, createTableString, -1, &createTableStatement, nil) ==
            SQLITE_OK {
          // 3
          if sqlite3_step(createTableStatement) == SQLITE_DONE {
            print("\nContact table created.")
          } else {
            print("\nContact table is not created.")
          }
        } else {
            print("\nCREATE TABLE statement is not prepared.")
        }
        // 4
        sqlite3_finalize(createTableStatement)

    }
    
    func insertRecord(asset: PHAsset) {
        let insertString = """
        insert into photos (uuid, hidden, width, height, location, mediaType) values ('\(asset.localIdentifier)', \(asset.isHidden), '\(asset.pixelWidth)', '\(asset.pixelHeight)',
        '\(asset.location)', '\(asset.mediaType.rawValue)');
        """
        
        var insertStatement: OpaquePointer?
        // 1
        if sqlite3_prepare_v2(db, insertString, -1, &insertStatement, nil) ==
            SQLITE_OK {
          let id: Int32 = 1
          let name: NSString = "Ray"
          // 2
          sqlite3_bind_int(insertStatement, 1, id)
          // 3
          sqlite3_bind_text(insertStatement, 2, name.utf8String, -1, nil)
          // 4
          if sqlite3_step(insertStatement) == SQLITE_DONE {
            print("\nSuccessfully inserted row.")
          } else {
            print("\nCould not insert row.")
          }
        } else {
          print("\nINSERT statement is not prepared.")
        }
        // 5
        sqlite3_finalize(insertStatement)

    }
    
    func photoLibraryDidChange(_ changeInstance: PHChange) {
        if let changes = changeInstance.changeDetails(for: fetchResult) {
            fetchResult = changes.fetchResultAfterChanges
            if changes.hasIncrementalChanges {
                // If there are incremental diffs, animate them in the collection view.

                if let removed = changes.removedIndexes, removed.count > 0 {
                    print(removed)
//                        collectionView.deleteItems(at: removed.map { IndexPath(item: $0, section:0) })
                }
                if let inserted = changes.insertedIndexes, inserted.count > 0 {
                    print(inserted)
//                    collectionView.insertItems(at: inserted.map { IndexPath(item: $0, section:0) })
                }
                if let changed = changes.changedIndexes, changed.count > 0 {
                    print(changed)
//                    collectionView.reloadItems(at: changed.map { IndexPath(item: $0, section:0) })
                }
            }
        }
    }
    
    deinit {
        PHPhotoLibrary.shared().unregisterChangeObserver(self)
    }
}
