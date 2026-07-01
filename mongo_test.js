print('\n--- Latihan 1: Update view_course ---');
printjson(db.activity_logs.updateMany({action: 'view_course'}, {$set: {reviewed: true}}));

print('\n--- Latihan 1: Delete action test ---');
printjson(db.activity_logs.deleteMany({action: 'test'}));

print('\n--- Latihan 1: Count total docs ---');
print(db.activity_logs.countDocuments({}));

print('\n--- Latihan 1: Count per action ---');
printjson(db.activity_logs.aggregate([{$group: {_id: '$action', count: {$sum: 1}}}]).toArray());

print('\n--- Latihan 4: Explain dengan Index ---');
// Menggunakan user_id sembarang yang ada di database, misal 25
var explainPlan = db.activity_logs.find({user_id: 25}).sort({timestamp: -1}).explain('executionStats');
print("totalDocsExamined: " + explainPlan.executionStats.totalDocsExamined);
print("executionTimeMillis: " + explainPlan.executionStats.executionTimeMillis);
