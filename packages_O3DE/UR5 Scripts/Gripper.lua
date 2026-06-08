local Gripper =
{
	Properties =
	{
		ParentEntity = EntityId(),
		LeftEmitter = EntityId(),
		RightEmitter = EntityId(),
		RaycastDistance = 2.0,
	}
}

function Gripper:OnActivate()
	self.tickHandler = TickBus.Connect(self)
	
	self.otherLeft = nil;
	self.otherRight = nil;
	self.attachedObj = nil;
	self.attachedOgParent = nil;
	self.attachedObjOffset = nil;
end

function Gripper:OnDeactivate()
	-- Gripper handlers
	if (self.tickBusHandler ~= nil) then 
		self.tickHandler:Disconnect()
		self.tickHandler = nil
	end
	
	if (self.rigidBodyHandler ~= nil) then 
		self.rigidBodyHandler:Disconnect();
		self.rigidBodyHandler = nil;
	end
end

function Gripper:OnTick(deltaTime, framePoint)
	-- Get direction between emitters (and normalize it)
	local leftEmitterPos = TransformBus.Event.GetWorldTranslation(self.Properties.LeftEmitter)
	local rightEmitterPos = TransformBus.Event.GetWorldTranslation(self.Properties.RightEmitter)
	
	local leftDirection = rightEmitterPos - leftEmitterPos;
	local rightDirection = leftEmitterPos - rightEmitterPos;
	
	Vector3.Normalize(leftDirection);
	Vector3.Normalize(rightDirection);
	
	-- Fetch scene
	local physicsSystem = GetPhysicsSystem();
	local sceneHandle = physicsSystem:GetSceneHandle(DefaultPhysicsSceneName);
	local scene = physicsSystem:GetScene(sceneHandle);

	-- Request raycasts
	local leftRequest = RayCastRequest();
	leftRequest.Start = leftEmitterPos;
	leftRequest.Direction = leftDirection;
	leftRequest.Distance = self.Properties.RaycastDistance;
	leftRequest.ReportMultipleHits = false;
	
	local leftHits = scene:QueryScene(leftRequest);
	
	local rightRequest = RayCastRequest();
	rightRequest.Start = rightEmitterPos;
	rightRequest.Direction = rightDirection;
	rightRequest.Distance = self.Properties.RaycastDistance;
	rightRequest.ReportMultipleHits = false;
	
	local rightHits = scene:QueryScene(rightRequest);
	
	-- Check for hits
	if leftHits.HitArray:Size() ~= 0 and tostring(ComponentApplicationBus.Broadcast.GetEntityName(leftHits.HitArray[0].EntityId)) == "Box" then
		Debug.Log("Found at left "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(leftHits.HitArray[0].EntityId)));
		self.otherLeft = leftHits.HitArray[0].EntityId;
	else
		self.otherLeft = nil;
	end
	
	if rightHits.HitArray:Size() ~= 0 and tostring(ComponentApplicationBus.Broadcast.GetEntityName(rightHits.HitArray[0].EntityId)) == "Box"  then
		Debug.Log("Found at right "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(rightHits.HitArray[0].EntityId)));
		self.otherRight = rightHits.HitArray[0].EntityId;
	else
		self.otherRight = nil;
	end
	
	Gripper:CheckAttach();

	if self.attachedObj ~= nil then
		TransformBus.Event.SetLocalTranslation(self.attachedObj, self.attachedObjOffset);
	end
end

function Gripper:CheckAttach()
	if self.otherLeft == self.otherRight and self.attachedObj == nil and self.otherLeft ~= nil then
		self.attachedObj = self.otherLeft;
		self.attachedOgParent = TransformBus.Event.GetParentId(self.attachedObj);
		Debug.Log("Attaching to " ..tostring(ComponentApplicationBus.Broadcast.GetEntityName(self.attachedObj)));
		TransformBus.Event.SetParent(self.attachedObj, self.Properties.ParentEntity);
		RigidBodyRequestBus.Event.SetGravityEnabled(self.attachedObj, false);
		self.attachedObjOffset = TransformBus.Event.GetLocalTranslation(self.attachedObj);
		
	elseif (self.otherLeft ~= self.otherRight or self.otherLeft == nil or self.otherRight == nil) and self.attachedObj ~= nil then
		TransformBus.Event.SetParent(self.attachedObj, self.attachedOgParent);
		RigidBodyRequestBus.Event.SetGravityEnabled(self.attachedObj, true);
		Debug.Log("Dettaching from " ..tostring(ComponentApplicationBus.Broadcast.GetEntityName(self.attachedObj)));
		self.attachedObj = nil;
		self.attachedOgParent = nil;
		self.attachedObjOffset = nil;
	end
end

return Gripper
