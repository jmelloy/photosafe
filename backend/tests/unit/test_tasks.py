"""Unit tests for task processing system"""

import pytest
from datetime import datetime, timezone
from app.models import Task, PlaceSummary
from cli.task_commands import (
    create_task,
    update_task_progress,
    mark_task_running,
    mark_task_completed,
    mark_task_failed,
)


@pytest.mark.unit
class TestTaskModel:
    """Test Task model functionality"""

    def test_create_task(self, db_session):
        """Test creating a task record"""
        task = Task(
            name="Test Task",
            task_type="test",
            status="pending",
            progress=0,
            total=100,
            processed=0,
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.id is not None
        assert task.name == "Test Task"
        assert task.task_type == "test"
        assert task.status == "pending"
        assert task.progress == 0
        assert task.processed == 0
        assert task.total == 100
        assert task.created_at is not None

    def test_task_helper_functions(self, db_session):
        """Test task helper functions"""
        # Create task
        task = create_task(db_session, "Test Task", "test", total=100)
        assert task.id is not None
        assert task.status == "pending"

        # Mark as running
        mark_task_running(db_session, task)
        db_session.refresh(task)
        assert task.status == "running"
        assert task.started_at is not None

        # Update progress
        update_task_progress(db_session, task, 50)
        db_session.refresh(task)
        assert task.processed == 50
        assert task.progress == 50

        # Mark as completed
        mark_task_completed(db_session, task)
        db_session.refresh(task)
        assert task.status == "completed"
        assert task.completed_at is not None
        assert task.progress == 100

    def test_task_failure(self, db_session):
        """Test marking task as failed"""
        task = create_task(db_session, "Test Task", "test")
        mark_task_running(db_session, task)

        error_msg = "Something went wrong"
        mark_task_failed(db_session, task, error_msg)
        db_session.refresh(task)

        assert task.status == "failed"
        assert task.error_message == error_msg
        assert task.completed_at is not None


@pytest.mark.unit
class TestPlaceSummaryModel:
    """Test PlaceSummary model functionality"""

    def test_create_place_summary(self, db_session):
        """Test creating a place summary record"""
        summary = PlaceSummary(
            place_name="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            photo_count=50,
            first_photo_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
            last_photo_date=datetime(2024, 12, 1, tzinfo=timezone.utc),
            country="United States",
            state_province="California",
            city="San Francisco",
            place_data={
                "name": "San Francisco",
                "country": "United States",
                "admin1": "California",
            },
        )
        db_session.add(summary)
        db_session.commit()
        db_session.refresh(summary)

        assert summary.id is not None
        assert summary.place_name == "San Francisco"
        assert summary.latitude == 37.7749
        assert summary.longitude == -122.4194
        assert summary.photo_count == 50
        assert summary.country == "United States"
        assert summary.state_province == "California"
        assert summary.city == "San Francisco"
        assert summary.updated_at is not None

    def test_place_summary_unique_constraint(self, db_session):
        """Test that place_name is unique"""
        summary1 = PlaceSummary(
            place_name="New York",
            photo_count=10,
        )
        db_session.add(summary1)
        db_session.commit()

        # Try to create another with same name
        summary2 = PlaceSummary(
            place_name="New York",
            photo_count=20,
        )
        db_session.add(summary2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()


@pytest.mark.unit
class TestTaskAPI:
    """Test task API endpoints"""

    def test_get_tasks(self, client, auth_token, db_session):
        """Test getting list of tasks"""
        # Create some tasks
        task1 = Task(name="Task 1", task_type="test", status="pending")
        task2 = Task(name="Task 2", task_type="test", status="completed")
        db_session.add_all([task1, task2])
        db_session.commit()

        # Get all tasks
        response = client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2

    def test_get_task_by_id(self, client, auth_token, db_session):
        """Test getting a specific task"""
        task = Task(name="Test Task", task_type="test", status="pending")
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.get(
            f"/api/tasks/{task.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task.id
        assert data["name"] == "Test Task"

    def test_get_tasks_with_filters(self, client, auth_token, db_session):
        """Test filtering tasks by status and type"""
        task1 = Task(name="Task 1", task_type="lookup_places", status="pending")
        task2 = Task(
            name="Task 2", task_type="update_place_summary", status="completed"
        )
        task3 = Task(name="Task 3", task_type="lookup_places", status="completed")
        db_session.add_all([task1, task2, task3])
        db_session.commit()

        # Filter by status
        response = client.get(
            "/api/tasks?status=completed",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2

        # Filter by task_type
        response = client.get(
            "/api/tasks?task_type=lookup_places",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2


@pytest.mark.unit
class TestPlaceSummaryAPI:
    """Test place summary API endpoints"""

    def test_get_place_summaries(self, client, auth_token, db_session):
        """Test getting list of place summaries"""
        # Create some summaries
        summary1 = PlaceSummary(
            place_name="Paris",
            country="France",
            photo_count=30,
        )
        summary2 = PlaceSummary(
            place_name="London",
            country="United Kingdom",
            photo_count=20,
        )
        db_session.add_all([summary1, summary2])
        db_session.commit()

        response = client.get(
            "/api/place-summaries",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        summaries = response.json()
        assert len(summaries) == 2

    def test_get_place_summary_by_id(self, client, auth_token, db_session):
        """Test getting a specific place summary"""
        summary = PlaceSummary(
            place_name="Tokyo",
            country="Japan",
            photo_count=50,
        )
        db_session.add(summary)
        db_session.commit()
        db_session.refresh(summary)

        response = client.get(
            f"/api/place-summaries/{summary.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == summary.id
        assert data["place_name"] == "Tokyo"
        assert data["country"] == "Japan"

    def test_filter_place_summaries_by_country(self, client, auth_token, db_session):
        """Test filtering place summaries by country"""
        summary1 = PlaceSummary(place_name="NYC", country="USA", photo_count=40)
        summary2 = PlaceSummary(place_name="LA", country="USA", photo_count=30)
        summary3 = PlaceSummary(place_name="Paris", country="France", photo_count=20)
        db_session.add_all([summary1, summary2, summary3])
        db_session.commit()

        response = client.get(
            "/api/place-summaries?country=USA",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        summaries = response.json()
        assert len(summaries) == 2
        assert all(s["country"] == "USA" for s in summaries)

    def test_place_summary_pagination(self, client, auth_token, db_session):
        """Test pagination of place summaries"""
        # Create multiple summaries
        for i in range(15):
            summary = PlaceSummary(
                place_name=f"Place {i}",
                photo_count=i,
            )
            db_session.add(summary)
        db_session.commit()

        # Get first page
        response = client.get(
            "/api/place-summaries?limit=10&offset=0",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        summaries = response.json()
        assert len(summaries) == 10

        # Get second page
        response = client.get(
            "/api/place-summaries?limit=10&offset=10",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        summaries = response.json()
        assert len(summaries) == 5
