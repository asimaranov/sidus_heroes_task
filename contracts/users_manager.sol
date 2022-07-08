contract UsersManager {

    mapping(uint => string) public users;
    event UserCreated(uint user_id, string username);

    function notifyUserCreated(uint user_id, string memory username) public {
        users[user_id] = username;
        emit UserCreated(user_id, username);
    }

}
