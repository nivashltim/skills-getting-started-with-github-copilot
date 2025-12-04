"""
Unit tests for the FastAPI application.
"""
import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoint."""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        
    def test_activity_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
    def test_activities_have_participants(self, client):
        """Test that activities contain participant data"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert chess_club["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


class TestSignupEndpoint:
    """Tests for the signup endpoint."""
    
    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to activity"""
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        assert "newstudent@mergington.edu" in chess_club["participants"]
        assert len(chess_club["participants"]) == 3
        
    def test_signup_nonexistent_activity(self, client):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_signup_duplicate_student(self, client):
        """Test that student cannot sign up twice for same activity"""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        
    def test_signup_student_already_registered(self, client):
        """Test that already registered student cannot signup again"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint."""
    
    def test_unregister_successful(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant from activity"""
        client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        assert "michael@mergington.edu" not in chess_club["participants"]
        assert len(chess_club["participants"]) == 1
        
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_unregister_student_not_registered(self, client):
        """Test that unregistering non-registered student returns error"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
        
    def test_unregister_last_participant(self, client):
        """Test unregistering the last participant from an activity"""
        # Basketball Team has only one participant
        response = client.delete(
            "/activities/Basketball Team/unregister?email=james@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant is removed
        activities_response = client.get("/activities")
        basketball = activities_response.json()["Basketball Team"]
        assert len(basketball["participants"]) == 0


class TestSignupAndUnregisterFlow:
    """Integration tests for signup and unregister flow."""
    
    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering"""
        email = "testuser@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregister
        final_response = client.get("/activities")
        assert email not in final_response.json()[activity]["participants"]
        
    def test_multiple_signups_and_unregisters(self, client):
        """Test multiple signup and unregister operations"""
        activity = "Programming Class"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Sign up all students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all signed up
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants
        
        # Unregister half of them
        for email in emails[:2]:
            response = client.delete(f"/activities/{activity}/unregister?email={email}")
            assert response.status_code == 200
        
        # Verify unregistration
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert emails[0] not in participants
        assert emails[1] not in participants
        assert emails[2] in participants
